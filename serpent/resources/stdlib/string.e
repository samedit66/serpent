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
    -- Данный метод здесь определен только для того, чтобы
    -- обеспечить удобную работу с методом print из класса IO.
        external "Java"
        alias "com.eiffel.PLATFORM.STRING_to_string"
    end
end
