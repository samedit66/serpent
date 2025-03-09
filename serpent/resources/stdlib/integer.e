class
    INTEGER

inherit
    COMPARABLE

feature

    plus (other: like Current): like Current
        -- Сложение чисел. Псевдоним для '+'
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_plus"
    end

    to_real: REAL
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_to_real"
    end

    is_less (other: like Current): BOOLEAN
    -- Вычитание чисел. Псевдоним для '-'
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_is_less"
    end

    is_equal (other: like Current): BOOLEAN
        -- Вычитание чисел. Псевдоним для '-'
        external "Java"
        alias "com.eiffel.PLATFORM.INTEGER_is_equal"
    end
end
