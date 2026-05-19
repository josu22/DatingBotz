"""
Modelo de preferencia visual de fotos de perfiles.

Flujo de uso:
  1. Recopilar datos:  session.collect_training_data(n=100)
  2. Entrenar:         session.train_preference_model()
  3. Usar en likes:    session.like(amount=500, photo_model_threshold=0.4)

El clasificador usa transfer learning: extrae embeddings con ResNet18 (torchvision)
o con DeepFace Facenet como fallback, y entrena una LogisticRegression de sklearn.
Con ~100 muestras es más que suficiente para el clasificador lineal.
"""
import os
import pickle
import tempfile
import numpy as np
from pathlib import Path
from typing import Callable, Optional, Tuple

_SUPPORTED_EXTS = ('.jpg', '.jpeg', '.png', '.webp')
_DEFAULT_MODEL_PATH = os.path.join('data', 'models', 'preference_model.pkl')


def _list_images(directory: Path):
    imgs = []
    for ext in _SUPPORTED_EXTS:
        imgs.extend(directory.glob(f'*{ext}'))
    return imgs


def _load_extractor() -> Tuple[Callable, int]:
    """
    Carga el extractor de embeddings.
    Intenta torchvision ResNet18 (512-dim) primero; si no está disponible,
    usa DeepFace Facenet (128-dim), que ya está en requirements.txt.
    Devuelve (fn_extraer: path -> ndarray | None, dim: int).
    """
    try:
        import torch
        from torchvision import models, transforms
        from PIL import Image as _PILImage

        try:
            backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        except AttributeError:
            backbone = models.resnet18(pretrained=True)
        backbone.fc = torch.nn.Identity()
        backbone.eval()

        tfm = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        def _extract_torch(path: str) -> Optional[np.ndarray]:
            try:
                img = _PILImage.open(path).convert('RGB')
                with torch.no_grad():
                    return backbone(tfm(img).unsqueeze(0)).squeeze().numpy()
            except Exception:
                return None

        return _extract_torch, 512

    except ImportError:
        pass

    try:
        from deepface import DeepFace

        def _extract_deepface(path: str) -> Optional[np.ndarray]:
            try:
                result = DeepFace.represent(
                    img_path=path,
                    model_name='Facenet',
                    enforce_detection=False,
                )
                emb = result[0]['embedding'] if isinstance(result, list) else result['embedding']
                return np.array(emb, dtype=float)
            except Exception:
                return None

        return _extract_deepface, 128

    except ImportError:
        raise ImportError(
            "Se necesita torchvision (pip install torch torchvision) "
            "o deepface (pip install deepface) para el modelo de preferencia visual."
        )


def _download_image(url: str, dest_path: str) -> bool:
    try:
        import requests
        resp = requests.get(url, timeout=8, stream=True)
        resp.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return True
    except Exception:
        return False


class PhotoPreferenceModel:
    """
    Clasificador binario de preferencia visual (like / dislike).

    Ejemplo:
        model = PhotoPreferenceModel()
        stats = model.train('data/training')
        # {'accuracy': 0.78, 'n_liked': 60, 'n_disliked': 40, 'n_total': 100}

        liked, score = model.predict_from_url('https://images-ssl.gotinder.com/...')
    """

    def __init__(self, model_path: str = _DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self._pipeline = None
        self._extract: Optional[Callable] = None

    def _get_extractor(self) -> Callable:
        if self._extract is None:
            self._extract, _ = _load_extractor()
        return self._extract

    # ------------------------------------------------------------------
    # Entrenamiento
    # ------------------------------------------------------------------

    def train(self, training_dir: str = 'data/training') -> dict:
        """
        Entrena el clasificador con imágenes etiquetadas en subdirectorios:
          training_dir/liked/    → positivos (fotos que gustaron)
          training_dir/disliked/ → negativos (fotos que no gustaron)

        Guarda el modelo en self.model_path y devuelve métricas.
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import cross_val_score

        extract = self._get_extractor()
        base = Path(training_dir)

        X, y = [], []
        for label, subdir in ((1, 'liked'), (0, 'disliked')):
            d = base / subdir
            if not d.exists():
                continue
            for img_path in _list_images(d):
                feats = extract(str(img_path))
                if feats is not None:
                    X.append(feats)
                    y.append(label)

        n_liked = int(sum(y))
        n_disliked = len(y) - n_liked

        if len(X) < 10:
            raise ValueError(
                f"Imágenes válidas encontradas: {len(X)} (mínimo 10). "
                f"Liked: {n_liked} | Disliked: {n_disliked}."
            )

        X_arr = np.array(X)
        y_arr = np.array(y)

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')),
        ])

        n_splits = min(5, min(n_liked, n_disliked))
        if n_splits >= 2:
            cv_scores = cross_val_score(pipeline, X_arr, y_arr, cv=n_splits)
            accuracy = float(cv_scores.mean())
        else:
            accuracy = 0.0

        pipeline.fit(X_arr, y_arr)
        self._pipeline = pipeline

        os.makedirs(os.path.dirname(os.path.abspath(self.model_path)), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(pipeline, f)

        return {
            'accuracy': round(accuracy, 3),
            'n_liked': n_liked,
            'n_disliked': n_disliked,
            'n_total': len(y),
        }

    # ------------------------------------------------------------------
    # Carga / persistencia
    # ------------------------------------------------------------------

    def load(self) -> bool:
        """Carga el modelo guardado. Devuelve True si tuvo éxito."""
        if not os.path.exists(self.model_path):
            return False
        try:
            with open(self.model_path, 'rb') as f:
                self._pipeline = pickle.load(f)
            return True
        except Exception:
            return False

    def is_ready(self) -> bool:
        return self._pipeline is not None

    # ------------------------------------------------------------------
    # Predicción
    # ------------------------------------------------------------------

    def predict_from_file(self, image_path: str, threshold: float = 0.5) -> Tuple[bool, float]:
        """
        Predice si la imagen gustaría.
        Devuelve (should_like: bool, score: float 0-1).
        Si el modelo no está cargado, devuelve (True, 0.5) para no bloquear.
        """
        if self._pipeline is None:
            return True, 0.5
        feats = self._get_extractor()(image_path)
        if feats is None:
            return True, 0.5
        score = float(self._pipeline.predict_proba([feats])[0][1])
        return score >= threshold, score

    def predict_from_url(self, url: str, threshold: float = 0.5) -> Tuple[bool, float]:
        """
        Descarga la imagen de `url` y predice preferencia.
        Devuelve (should_like: bool, score: float 0-1).
        """
        if self._pipeline is None:
            return True, 0.5
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            if not _download_image(url, tmp_path):
                return True, 0.5
            return self.predict_from_file(tmp_path, threshold)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
