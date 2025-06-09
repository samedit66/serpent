class
    STRING
-- Класс для представления строк. Обертка над типом String в Java.

inherit
    ANY redefine out, is_equal end
    COMPARABLE redefine out end

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
-- Доступ к символам.

    at, item (index: INTEGER): CHARACTER
    -- Возвращает символ под индексом index.
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_raw_item"
    end

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_is_less"
    end

    is_equal (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_is_equal"
    end

feature
-- Конвертация в другие типы.

    out: STRING
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
