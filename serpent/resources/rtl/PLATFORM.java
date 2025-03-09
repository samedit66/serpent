package com.eiffel;

import java.io.PrintStream;
import java.io.UnsupportedEncodingException;
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

    // Поля для представления массива значений PLATFORM
    public ArrayList<PLATFORM> raw_array;
    public int array_min_index;
    public int array_max_index;

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

    /**
     * Конструктор для создания массива значений PLATFORM.
     * Устанавливает диапазон допустимых индексов и инициализирует список для хранения элементов.
     *
     * @param min_index минимальный индекс массива
     * @param max_index максимальный индекс массива
     * @throws IllegalArgumentException если min_index больше max_index
     */
    public PLATFORM(int min_index, int max_index) {
        if (min_index > max_index) {
            throw new IllegalArgumentException("min_index cannot be greater than max_index");
        }

        value_type = ARRAY_TYPE;
        array_min_index = min_index;
        array_max_index = max_index;
        int cap = array_max_index - array_min_index + 1;
        raw_array = new ArrayList<>(cap);
    }

    public static void ANY_print(PLATFORM self) throws UnsupportedEncodingException {
        PrintStream out = new PrintStream(System.out, true, "UTF-8");

        int valtype = self.value_type;
        if ((valtype & BOOLEAN_TYPE) != 0) {
            out.println(self.raw_int == 1 ? "True" : "False");
        }
        else if ((valtype & INTEGER_TYPE) != 0) {
            out.println(self.raw_int);
        }
        else if ((valtype & REAL_TYPE) != 0) {
            out.println(self.raw_float);
        }
        else if ((valtype & STRING_TYPE) != 0) {
            out.println(self.raw_string);
        }
        else if ((valtype & OBJECT_TYPE) != 0) {
            out.println("Object");
        }
        else if ((valtype & OBJECT_TYPE) != 0) {
            out.println("Array");
        }
    }

    public static String STRING_concat(PLATFORM self, String other) {
        return self.raw_string + other;
    }

    public static int STRING_count(PLATFORM self) {
        return self.raw_string.length();
    }

    public static int INTEGER_plus(PLATFORM self, int other) {
        return self.raw_int + other;
    }

    /* ******************************************************** */
    /* Методы для класса INTEGER */

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

    /* ******************************************************** */
    /* Методы для класса ARRAY */
    public static PLATFORM ARRAY_make_filled_with(int lower, int upper, PLATFORM value) {
        if (lower > upper) {
            throw new IllegalArgumentException("'lower' index cannot be greater than 'upper'");
        }

        int value_type = ARRAY_TYPE;
        int cap = upper - lower + 1;
        var raw_array = new ArrayList<>(cap);
        for (int i = 0; i < raw_array.size(); i++) {
            raw_array.set(i, value);
        }
    }

    public static PLATFORM ARRAY_item_raw(int index) {
        return 
    }
}
