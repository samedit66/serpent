class
    STRING
-- Класс для представления строк. Обертка над типом String в Java.

inherit
    STRINGABLE

feature
-- Операции со строками.

    concat, plus (other: STRING): STRING
        -- Соединяет две строки в одну. Исходные строки не меняется.
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_concat"
    end

feature
-- Характеристики строки.

    count: INTEGER
        -- Количество символов в строке.
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_count"
    end

feature
-- Конвертация в другие типы.

    out, to_string: STRING
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_to_string"
    end

    to_integer: INTEGER
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_to_integer"
    end

    to_real: REAL
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_to_integer"
    end
end
