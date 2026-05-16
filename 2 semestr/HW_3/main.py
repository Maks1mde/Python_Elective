import json
import re
import os


class MorseExtendedConverter:
    """
    Загрузка из JSON
    """
    def __init__(self, file_path: str):
        self._sym_to_morse = {}
        self._morse_to_sym = {}
        self._load_table(file_path)

    def _load_table(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for section in ('morse_eng', 'morse_digits', 'morse_ops'):
            if section in data:
                self._sym_to_morse.update(data[section])

        # обратный словарь
        self._morse_to_sym = {v: k for k, v in self._sym_to_morse.items()}

    def to_morse(self, symbol: str) -> str:
        # Вернуть морзе-код
        return self._sym_to_morse[symbol]

    def from_morse(self, code: str) -> str:
        # Вернуть символ
        return self._morse_to_sym[code]

    def is_valid_symbol(self, symbol: str) -> bool:
        return symbol in self._sym_to_morse

    def is_valid_morse(self, code: str) -> bool:
        return code in self._morse_to_sym

    def __getitem__(self, key):
        return self.to_morse(key)

    def __call__(self, key):
        return self.to_morse(key)

    def __len__(self):
        return len(self._sym_to_morse)

    def __iter__(self):
        return iter(self._sym_to_morse.values())


class TextToMorseConverter:
    """
    Конвертирует текстовые строки в морзе-строку.
    """
    def __init__(self, converter: MorseExtendedConverter):
        self._converter = converter

    def text_to_morse(self, text: str) -> str:
        words = text.split()
        morse_parts = []
        for word in words:
            morse_word = ' '.join(self._converter.to_morse(ch) for ch in word)
            morse_parts.append(morse_word)
        return '   '.join(morse_parts)

    def morse_to_text(self, morse_str: str) -> str:
        """
        Преобразует строку морзе в текст.
        """
        words = morse_str.split('   ')
        result_words = []
        for word in words:
            if not word:
                continue
            chars = word.split()
            text_word = ''.join(self._converter.from_morse(ch) for ch in chars)
            result_words.append(text_word)
        return ' '.join(result_words)


class MorseNumber:
    _converter = None

    @classmethod
    def set_converter(cls, converter: MorseExtendedConverter):
        cls._converter = converter

    def __init__(self, value):
        if isinstance(value, int):
            self._value = value
        elif isinstance(value, str):
            parts = value.split()
            digits = []
            for part in parts:
                if not MorseNumber._converter.is_valid_morse(part):
                    raise ValueError(f"Неверный морзе-код цифры: {part}")
                sym = MorseNumber._converter.from_morse(part)
                if not sym.isdigit():
                    raise ValueError(f"Символ {sym} не является цифрой")
                digits.append(sym)
            self._value = int(''.join(digits))
        else:
            raise TypeError("value должен быть int или str")

    def __int__(self):
        return self._value

    def __str__(self):
        digits = str(self._value)
        codes = [MorseNumber._converter.to_morse(d) for d in digits]
        return ' '.join(codes)

    def __repr__(self):
        return f"MorseNumber({self._value})"

    # Арифметические операции
    def __add__(self, other):
        if not isinstance(other, MorseNumber):
            other = MorseNumber(other)
        return MorseNumber(self._value + other._value)

    def __sub__(self, other):
        if not isinstance(other, MorseNumber):
            other = MorseNumber(other)
        return MorseNumber(self._value - other._value)

    def __mul__(self, other):
        if not isinstance(other, MorseNumber):
            other = MorseNumber(other)
        return MorseNumber(self._value * other._value)

    def __truediv__(self, other):
        if not isinstance(other, MorseNumber):
            other = MorseNumber(other)
        if other._value == 0:
            raise ZeroDivisionError("Деление на ноль")
        return MorseNumber(self._value // other._value)

    def __floordiv__(self, other):
        return self.__truediv__(other)

    # Сравнения
    def __eq__(self, other):
        if not isinstance(other, MorseNumber):
            other = MorseNumber(other)
        return self._value == other._value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, MorseNumber):
            other = MorseNumber(other)
        return self._value < other._value

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)

    def __neg__(self):
        return MorseNumber(-self._value)

    def __abs__(self):
        return MorseNumber(abs(self._value))


class MorseCalculator:
    """
    Обрабатывает строки разных типов:
    """
    def __init__(self, converter: MorseExtendedConverter):
        self._converter = converter
        self._text_converter = TextToMorseConverter(converter)

    def _evaluate_expression(self, expr_str: str) -> int:
        """
        Вычисляет арифметическое выражение
        """
        # Удаляем пробелы, оставляем только цифры и операторы
        clean_expr = ''.join(expr_str.split())
        # Проверяем допустимые символы
        if not re.fullmatch(r'[\d+\-*/]+', clean_expr):
            raise ValueError(f"Недопустимое выражение: {expr_str}")
        # Безопасное вычисление
        return eval(clean_expr, {"__builtins__": None}, {})

    def _number_to_result(self, num: int) -> str:
        # Преобразует число в морзе
        morse_num = MorseNumber(num)
        return f"{morse_num} ({num})"

    def process(self, text: str) -> str:
        if any(ch.isalpha() for ch in text):
            return self._text_converter.text_to_morse(text)

        parts = text.split('=')
        parts = [p.strip() for p in parts]

        if len(parts) == 1:
            return self._text_converter.text_to_morse(parts[0])

        result_parts = []

        for i in range(len(parts) - 1):
            expr = parts[i]
            if expr == '':
                continue
            try:
                value = self._evaluate_expression(expr)
                result_parts.append(self._number_to_result(value))
            except Exception as e:
                result_parts.append(self._text_converter.text_to_morse(expr))

        last = parts[-1]
        if last:
            result_parts.append(self._text_converter.text_to_morse(last))

        return '   '.join(result_parts)


def run_tests(calculator: MorseCalculator):
    tests = [
        ("hello world", ".... . .-.. .-.. ---   .-- --- .-. .-.. -.."),
        ("student", "... - ..- -.. . -. -"),

        ("abc 123", ".- -... -.-.   .---- ..--- ...--"),
        ("student of 2026", "... - ..- -.. . -. -   --- ..-.   ..--- ----- ..--- -...."),

        ("2 + 3", "..---   .-.-.   ...--"),
        ("20 * 3", "..--- -----   -..-   ...--"),

        ("4 + 3 = ", "--... (7)"),
        ("2 + 3 * 4 = ", ".---- ....- (14)"),

        ("2 + 2 = 3 + 3 = 5 + 5", "....- (4)   -.... (6)   .....   .-.-.   ....."),
        ("= 10 + 10", ".---- -----   .-.-.   .---- -----"),
    ]

    print("Запуск тестов:\n")
    for i, (input_text, expected) in enumerate(tests, 1):
        result = calculator.process(input_text)
        print(f"Тест {i}")
        print(f"  Вход: {input_text}")
        print(f"  Ожидание:  {expected}")
        print(f"  Результат: {result}")
        print()


def main():
    # Загружаем конвертер
    converter = MorseExtendedConverter('morse.json')

    # Устанавливаем конвертер
    MorseNumber.set_converter(converter)

    # Создаём калькулятор
    calculator = MorseCalculator(converter)

    # Запускаем тесты
    run_tests(calculator)


if __name__ == "__main__":
    main()