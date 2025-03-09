class REAL
feature
    plus (other: like Current): like Current
        -- Сложение чисел. Псевдоним для '+'
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_plus"
    end

    is_equal (other: like Current): BOOLEAN
        -- Вычитание чисел. Псевдоним для '-'
        external "Java"
        alias "com.eiffel.PLATFORM.REAL_is_equal"
    end
end
