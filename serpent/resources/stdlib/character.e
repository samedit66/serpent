class
    CHARACTER
-- Символьный тип. В отличие от типа char в Java представляет
-- из себя unicode code point - следовательно, его размер варьируется от
-- 1 до 4-х байтов.

inherit
    ANY redefine out, is_equal end
    COMPARABLE redefine out end
    HASHABLE redefine out end

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
    then
        code_point < other.code_point
    end

    is_equal (other: like Current): BOOLEAN
    then
        code_point = other.code_point
    end

feature
-- Характеристики.

    hash_code: INTEGER
    -- Хэш-код.
    then
        code_point
    end

    code_point: INTEGER
    -- code point для данного символа.
        external "Java"
        alias "com.eiffel.PLATFORM.CHARACTER_code_point"
    end

    is_digit: BOOLEAN
    -- Является ли текущий символ цифрой от 0 до 9?
    local
        possible_digit: INTEGER
    do
        possible_digit := code_point - '0'.code_point
        Result := possible_digit.in_range (0, 9)
    end

    is_space: BOOLEAN
    -- Является ли символ пробельным?
    then
        Current = ' '
        or else Current = '%T'
        or else Current = '%N'
    end

feature
-- Конвертация в другие типы.

    out: STRING
        external "Java"
        alias "com.eiffel.PLATFORM.CHARACTER_to_string"
    end

    as_digit, to_integer: INTEGER
    do
        require_that (is_digit, "Character does not represent a digit")
        Result := code_point - '0'.code_point
    end

end
