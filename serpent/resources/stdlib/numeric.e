deferred class
    NUMERIC
-- Родитель всех числовых типов. Опрелеляет набор математических операций,
-- которые доступны над всеми числами.

feature
-- Арифметические действия.

    plus (other: like Current): like Current
        -- Сложение чисел. Псевдоним для '+'.
        deferred
    end

    minus (other: like Current): like Current
        -- Вычитание чисел. Псевдоним для '-'.
        deferred
    end

    product (other: like Current): like Current
        -- Умножение чисел. Псевдоним для '*'.
        deferred
    end

    quotient (other: like Current): REAL
        -- Деление чисел. Псевдоним для "/".
        deferred
    end

    identity: like Current
        -- Унарные плюс. Псевдоним для "+".
        deferred
    end

    opposite: like Current
        -- Унарный минус. Псевдоним для "-".
        deferred
    end

    abs: like Current
        -- Модуль числа.
        deferred
    end

end
