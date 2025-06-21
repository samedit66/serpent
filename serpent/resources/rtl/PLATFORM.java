package com.eiffel;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

/**
 * Класс PLATFORM представляет универсальное значение для системы Eiffel.
 * Он поддерживает хранение целых чисел, вещественных чисел, строк, символов Unicode и массивов,
 * что позволяет использовать единый интерфейс для работы с данными различных типов.
 */
public class PLATFORM {

    // Флаги типов данных
    public static final int INTEGER_TYPE     = 1;
    public static final int REAL_TYPE        = 1 << 1;
    public static final int STRING_TYPE      = 1 << 2;
    public static final int CHARACTER_TYPE   = 1 << 3;
    public static final int BOOLEAN_TYPE     = 1 << 4;
    public static final int ARRAY_TYPE       = 1 << 5;
    public static final int OBJECT_TYPE      = 1 << 6;

    /**
     * Флаг, определяющий тип значения.
     */
    public int value_type;

    // Поля для хранения значений примитивных типов
    public int raw_int;
    public float raw_float;
    public String raw_string;

    // Аргументы командной строки.
    public static String[] command_line_args;

    public static void setArgs(String[] args) {
        command_line_args = args;
    }

    // Поля для представления массива значений PLATFORM
    public ArrayList<PLATFORM> raw_array;

    public PLATFORM() {
        value_type = OBJECT_TYPE;
    }

    /**
     * Конструктор для целочисленного значения.
     * При значениях 0 и 1 помечает значение как логическое (BOOLEAN_TYPE) в value_type.
     *
     * @param integer_value целочисленное значение
     */
    public PLATFORM(int integer_value) {
        value_type = INTEGER_TYPE;
        raw_int = integer_value;
        // Логический тип определяется по значению 0 или 1, дополнительного поля не требуется.
        if (integer_value == 0 || integer_value == 1) {
            value_type |= BOOLEAN_TYPE;
        }
    }

    /**
     * Конструктор для вещественного значения.
     *
     * @param real_value вещественное число
     */
    public PLATFORM(float real_value) {
        value_type = REAL_TYPE;
        raw_float = real_value;
    }

    /**
     * Конструктор для строкового значения.
     *
     * @param string_value строка
     */
    public PLATFORM(String string_value) {
        value_type = STRING_TYPE;
        raw_string = string_value;

        if (raw_string.codePointCount(0, raw_string.length()) == 1) {
            value_type |= CHARACTER_TYPE;
        }
    }

    public PLATFORM(ArrayList<PLATFORM> array) {
        value_type = ARRAY_TYPE;
        raw_array = array;
    }

    /* ******************************************************** */
    /* Методы для класса ARGUMENTS */
    public static int ARGUMENTS_argument_count(PLATFORM self) {
        return command_line_args.length;
    }

    public static String ARGUMENTS_argument(PLATFORM self, int i) {
        return command_line_args[i - 1];
    }

    /* ******************************************************** */
    /* Методы для класса ANY */

    public static void ANY_crash_with_message(PLATFORM self, String message) throws UnsupportedEncodingException {
        PrintStream err = new PrintStream(System.err, true, "UTF-8");
        err.println(message);
        System.exit(1);
    }

    public static void ANY_require_that(PLATFORM self, int condition, String message) throws PreconditionFailedException {
        if (condition != 1)
            throw new PreconditionFailedException(message);
    }

    public static int ANY_is_void(PLATFORM self, PLATFORM other) {
        return other == null ? 1 : 0;
    }

    public static int ANY_is_same(PLATFORM self, PLATFORM other) {
        return other == self ? 1 : 0;
    }

    public static String ANY_out(PLATFORM self) {
        return self.toString();
    }

    /* ******************************************************** */
    /* Методы для класса STRING */

    public static String STRING_concat(PLATFORM self, String other) {
        return self.raw_string + other;
    }

    public static int STRING_count(PLATFORM self) {
        return self.raw_string.codePointCount(0, self.raw_string.length());
    }

    public static String STRING_to_string(PLATFORM self) {
        return new String(self.raw_string);
    }

    public static int three_way_comparison(String s1, String s2) {
        int index1 = 0;
        int index2 = 0;
        while (index1 < s1.length() && index2 < s2.length()) {
            int cp1 = s1.codePointAt(index1);
            int cp2 = s2.codePointAt(index2);
            if (cp1 != cp2) {
                return cp1 - cp2;
            }
            index1 += Character.charCount(cp1);
            index2 += Character.charCount(cp2);
        }
        // Если все codepoint совпадают, то строка с оставшимися символами считается большей.
        if (index1 < s1.length()) {
            return 1;
        }
        if (index2 < s2.length()) {
            return -1;
        }
        return 0;
    }

    public static int STRING_is_less(PLATFORM self, String other) {
        return three_way_comparison(self.raw_string, other) < 0 ? 1 : 0;
    }

    public static int STRING_is_equal(PLATFORM self, String other) {
        return three_way_comparison(self.raw_string, other) == 0 ? 1 : 0;
    }

    public static String STRING_raw_item(PLATFORM self, int index) {
        index -= 1;

        if (index < 0 || index >= self.raw_string.codePointCount(0, self.raw_string.length())) {
            throw new IndexOutOfBoundsException("Index " + index + " out of bounds");
        }

        int offset = 0;
        int currentIndex = 0;
        while (currentIndex < index) {
            offset += Character.charCount(self.raw_string.codePointAt(offset));
            currentIndex++;
        }

        int codePoint = self.raw_string.codePointAt(offset);
        return new String(Character.toChars(codePoint));
    }

    public static int STRING_hash_code(PLATFORM self) {
        return self.raw_string.hashCode();
    }

    /* ******************************************************** */
    /* Методы для класса INTEGER */

    public static int INTEGER_plus(PLATFORM self, int other) {
        return self.raw_int + other;
    }

    public static int INTEGER_minus(PLATFORM self, int other) {
        return self.raw_int - other;
    }

    public static int INTEGER_product(PLATFORM self, int other) {
        return self.raw_int * other;
    }

    public static float INTEGER_quotient(PLATFORM self, int other) {
        return ((float) self.raw_int) / other;
    }

    public static int INTEGER_identity(PLATFORM self) {
        return self.raw_int;
    }

    public static int INTEGER_opposite(PLATFORM self) {
        return -self.raw_int;
    }

    public static int INTEGER_integer_quotient(PLATFORM self, int other) {
        return self.raw_int / other;
    }

    public static int INTEGER_integer_remainder(PLATFORM self, int other) {
        return self.raw_int % other;
    }

    public static int INTEGER_is_less(PLATFORM self, int other) {
        return self.raw_int < other ? 1 : 0;
    }

    public static int INTEGER_is_equal(PLATFORM self, int other) {
        return self.raw_int == other ? 1 : 0;
    }

    public static float INTEGER_to_real(PLATFORM self) {
        return (float) self.raw_int;
    }

    public static String INTEGER_to_string(PLATFORM self) {
        return Integer.toString(self.raw_int);
    }

    public static String INTEGER_to_character(PLATFORM self) {
        return Character.toString(self.raw_int);
    }

    /* ******************************************************** */
    /* Методы для класса REAL */

    public static float REAL_plus(PLATFORM self, float other) {
        return self.raw_float + other;
    }

    public static float REAL_minus(PLATFORM self, float other) {
        return self.raw_float - other;
    }

    public static float REAL_product(PLATFORM self, float other) {
        return self.raw_float * other;
    }

    public static float REAL_quotient(PLATFORM self, float other) {
        return self.raw_float / other;
    }

    public static float REAL_identity(PLATFORM self) {
        return self.raw_float;
    }

    public static float REAL_opposite(PLATFORM self) {
        return -self.raw_float;
    }

    public static int REAL_is_less(PLATFORM self, float other) {
        return self.raw_float < other ? 1 : 0;
    }

    public static int REAL_is_equal(PLATFORM self, float other) {
        return self.raw_float == other ? 1 : 0;
    }

    public static String REAL_to_string(PLATFORM self) {
        String s = Float.toString(self.raw_float);

        // Убираем незначащие нули после запятой
        int index = s.length() - 1;
        while (index > 0 && s.charAt(index) == '0') {
            index--;
        }
        
        if (s.charAt(index) == '.') {
            index--;
        }

        return s.substring(0, index + 1);
    }

    /* ******************************************************** */
    /* Методы для класса ARRAY */

    public static void ARRAY_initialize(PLATFORM self, int count, PLATFORM value) {
        if (count < 0) {
            throw new IllegalArgumentException("'count' cannot be negative");
        }

        ArrayList<PLATFORM> array = new ArrayList<>(count);
        for (int i = 0; i < count; i++) {
            array.add(i, value);
        }

        self.value_type = ARRAY_TYPE;
        self.raw_array = array;
    }

    public static PLATFORM ARRAY_item_raw(PLATFORM self, int index) {
        return self.raw_array.get(index);
    }

    public static void ARRAY_put_raw(PLATFORM self, PLATFORM element, int index) {
        self.raw_array.set(index, element);
    }

    public static void ARRAY_add_raw(PLATFORM self, PLATFORM element, int index) {
        self.raw_array.add(index, element);
    }

    public static void ARRAY_add_last(PLATFORM self, PLATFORM element) {
        self.raw_array.add(self.raw_array.size(), element);
    }

    public static void ARRAY_remove_raw(PLATFORM self, int index) {
        self.raw_array.remove(index);
    }

    /* Методы для класса IO */

    private static final BufferedReader in =
        new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));

    public static void IO_put_string(PLATFORM self, String s) throws UnsupportedEncodingException {
        PrintStream out = new PrintStream(System.out, true, "UTF-8");
        out.print(s);
    }

    public static String IO_input_string(PLATFORM self) throws IOException {
        return in.readLine();
    }

    public static int IO_input_integer(PLATFORM self) throws IOException {
        String line = in.readLine();
        return Integer.parseInt(line.trim());
    }

    public static float IO_input_real(PLATFORM self) throws IOException {
        String line = in.readLine();
        return Float.parseFloat(line.trim());
    }

    public static String IO_input_character(PLATFORM self) throws IOException {
        int first = in.read();
        if (first == -1) {
            return "";
        }

        char ch = (char) first;
        int codepoint;
        if (Character.isHighSurrogate(ch)) {
            int second = in.read();
            if (second != -1) {
                char ch2 = (char) second;
                if (Character.isLowSurrogate(ch2)) {
                    codepoint = Character.toCodePoint(ch, ch2);
                } else {
                    codepoint = ch;
                }
            } else {
                codepoint = ch;
            }
        } else {
            codepoint = ch;
        }

        return new String(Character.toChars(codepoint));
    }

    /* Методы для класса CHARACTER */

    public static int CHARACTER_is_less(PLATFORM self, String other) {
        return STRING_is_less(self, other);
    }

    public static int CHARACTER_is_equal(PLATFORM self, String other) {
        return STRING_is_equal(self, other);
    }

    public static int CHARACTER_code_point(PLATFORM self) {
        return self.raw_string.codePointAt(0);
    }

    public static String CHARACTER_to_string(PLATFORM self) {
        return STRING_to_string(self);
    }

    /* Методы для класса BOOLEAN */
    
    public static int BOOLEAN_is_less(PLATFORM self, int other) {
        return INTEGER_is_less(self, other);
    }

    public static int BOOLEAN_is_equal(PLATFORM self, int other) {
        return INTEGER_is_equal(self, other);
    }

    public static String BOOLEAN_to_string(PLATFORM self) {
        return self.raw_int == 1 ? "True" : "False";
    }
}
