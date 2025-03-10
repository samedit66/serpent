class
    INTEGER
-- Целые числа. Обертка для типа int в Java.

inherit
    NUMERIC
    COMPARABLE
    STRINGABLE

feature
-- Арифметические действия.

    plus (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_plus"
    end

    minus (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_minus"
    end

    product (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_product"
    end

    quotient (other: like Current): REAL
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_quotient"
    end

    identity: like Current
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_identity"
    end

    opposite: like Current
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_opposite"
    end

feature
-- Арифметические действия, специфичиные для типа INTEGER.

    integer_quotient (other: like Current): like Current
        -- Целочисленное деление.
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_integer_quotient"
    end

    integer_remainder (other: like Current): like Current
    -- Остаток от деления.
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_integer_remainder"
    end

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_is_less"
    end

    is_equal (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_is_equal"
    end

feature
-- Конвертация в другие типы.

    to_real: REAL
    -- Конвертирует в действительное число.
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_to_real"
    end

    out, to_string: STRING
    -- Конвертирует в строку.
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_to_string"
    end
end
