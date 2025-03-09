class REAL
-- Действительные числа. Обертка для типа float в Java.

inherit
    NUMERIC
    COMPARABLE

feature
-- Арифметические действия.

    plus (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_plus"
    end

    minus (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_minus"
    end

    product (other: like Current): like Current
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_product"
    end

    quotient (other: like Current): REAL
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_quotient"
    end

    identity: like Current
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_identity"
    end

    opposite: like Current
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_opposite"
    end

feature
-- Операции сравнения.

    is_less (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_is_less"
    end

    is_equal (other: like Current): BOOLEAN
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_is_equal"
    end
end
