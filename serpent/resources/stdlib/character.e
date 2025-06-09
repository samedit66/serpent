class
    CHARACTER
-- Символьный тип. В отличие от типа char в Java представляет
-- из себя unicode code point - следовательно, его размер варьируется от
-- 1 до 4-х байтов.

inherit
    ANY redefine out, is_equal end
    COMPARABLE redefine out end

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.CHARACTER_is_less"
    end

    is_equal (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.CHARACTER_is_equal"
    end

feature
-- Характеристики.

    code_point: INTEGER
    -- code point для данного символа.
        external "Java"
        alias "com.eiffel.PLATFORM.CHARACTER_code_point"
    end

feature
-- Конвертация в другие типы.

    out: STRING
        external "Java"
        alias "com.eiffel.PLATFORM.CHARACTER_to_string"
    end
end
