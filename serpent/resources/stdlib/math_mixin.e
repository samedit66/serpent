deferred class
    MATH_MIXIN
-- Содержит основные математические алгоритмы для различных чисел.

inherit
    NUMERIC
    COMPARABLE

feature

    abs: like Current
    -- Определяет модуль числа.
    do
        Result := Current
        if Result < zero then
            Result := -Result
        end
    end

    sqrt: REAL
    -- Вычисляет квадратный корень.
    then
        sqrt_with_precision (0.00001)
    end

    sqrt_with_precision (precision: REAL): REAL
    -- Вычисляет квадратный корень с заданной погрешностью.
    local
        approx, better_approx: REAL
    do
        from
            approx := Current / 2.0
            better_approx := (approx + Current/approx) / 2
        until
            (better_approx - approx).abs < precision
        loop
            approx := better_approx
            better_approx := (approx + Current/approx) / 2
        end

        Result := better_approx
    end

    pow (power: NUMERIC): REAL
    -- Возводит `Current` в степень `power`.
    external "Java"
    alias "com.eiffel.PLATFORM.MATH_MIXIN_power"
    end

    hypot (b: like Current): REAL
    -- Считает гипотенузу.
    -- Пример: `3.hypot (4)`
    then
        (Current*Current + b*b).sqrt
    end

    sin: REAL
    -- Вычисляет синус (в радианах).
    external "Java"
    alias "com.eiffel.PLATFORM.MATH_MIXIN_sin"
    end

    cos: REAL
    -- Вычисляет косинус (в радианах). 
    external "Java"
    alias "com.eiffel.PLATFORM.MATH_MIXIN_cos"
    end

    tan: REAL
    -- Вычисляет тангенс (в радианах).
    then
        sin / cos
    end

end
