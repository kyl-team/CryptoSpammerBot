import random
import traceback

from pyrofork.errors import RPCError


def slice_array(arr: list, n: int):
    k, m = divmod(len(arr), n)
    slices = [arr[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]
    return slices


dictionary: dict[str, list[str]] = {
    'о': ['o', '0'],
    'с': ['c'],
    'з': ['3'],
    'а': ['a'],
    'р': ['p'],
    'в': ['8'],
    'х': ['x']
}


def obfuscate_text(text: str):
    words = []
    for word in text.split():
        if random.random() > 0.5:
            source = random.choice(list(dictionary.keys()))
            new_word = word.replace(source, random.choice(dictionary[source]))
            print(new_word)
            words.append(new_word)
        else:
            words.append(word)
    return ' '.join(words)


def format_exception(e: Exception) -> str:
    if isinstance(e, RPCError):
        return f'Telegram RPCError ({e.NAME}) <b>[{e.CODE} {e.ID}]</b> <i>{e.MESSAGE}</i>'

    return f'{type(e).__name__} ({type(e).__name__}, "{"\n".join(traceback.format_exception(e))}")'
