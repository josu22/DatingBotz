import enum


# Using enum class create enumerations
class Socials(enum.Enum):
    SNAPCHAT = "snapchat"
    INSTAGRAM = "instagram"
    PHONENUMBER = "phone"
    FACEBOOK = "facebook"


class Sexuality(enum.Enum):
    MEN = "Men"
    WOMEN = "Women"
    EVERYONE = "Everyone"


class Language(enum.Enum):
    ENGLISH = "English"
    AFRIKAANS = "Afrikaans"
    ARABIC = "Arabic"
    BULGARIAN = "Bulgarian"
    BOSNIAN = "Bosnian"
    CROATIAN = "Croatian"
    CZECH = "Czech"
    DANISH = "Danish"
    DUTCH = "Dutch"
    ESTONIAN = "Estonian"
    FINNISH = "Finnish"
    FRENCH = "French"
    GEORGIAN = "Georgian"
    GERMAN = "German"
    GREEK = "Greek"
    HINDI = "Hindi"
    HUNGARIAN = "Hungarian"
    INDONESIAN = "Indonesian"
    ITALIAN = "Italian"
    JAPANESE = "Japanese"
    KOREAN = "Korean"
    LATVIAN = "Latvian"
    LITHUANIAN = "Lithuanian"
    MACEDONIAN = "Macedonian"
    MALAY = "Malay"
    POLISH = "Polish"
    PORTUGUESE = "Portuguese"
    ROMANIAN = "Romanian"
    RUSSIAN = "Russian"
    SERBIAN = "Serbian"
    SPANISH = "Spanish"
    SLOVAK = "Slovak"
    SLOVENIAN = "Slovenian"
    SWEDISH = "Swedish"
    TAMIL = "Tamil"
    THAI = "Thai"
    TURKISH = "Turkish"
    UKRAINIAN = "Ukrainian"
    VIETNAMESE = "Vietnamese"
   
class Printouts(enum.Enum):
    BANNER = ''' 
         _____ _           _           _           _       
        |_   _(_)_ __   __| | ___ _ __| |__   ___ | |_ ____
          | | | | '_ \ / _` |/ _ \ '__| '_ \ / _ \| __|_  /
          | | | | | | | (_| |  __/ |  | |_) | (_) | |_ / / 
          |_| |_|_| |_|\__,_|\___|_|  |_.__/ \___/ \__/___|
        ----------------------------------------------------'''
    
    EXPLANATION = '''
Proyecto de automatización con Selenium. Revisa la documentación del repositorio
y configura credenciales solo mediante variables de entorno o archivos locales
que no subas al control de versiones.
'''
