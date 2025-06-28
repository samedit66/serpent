class
    STRING_BUFFER
-- Строковый буффер.

create
    make,
    make_from_string

feature {NONE}

    buffer: STRING
    -- Внутреннее хранилище.

feature
-- Создание.

    make
    -- Создает пустую изменяемую строку.
    do
        buffer := ""
    end

    make_from_string (s: STRING)
    -- Создает изменяемую строку из неизменяемой
    do
        buffer := ""
        append_string (s)
    end

feature
-- Изменение содержимого буффера (добавление элементов).

    append_character (c: CHARACTER)
    -- Добавляет символ к концу строки.
    do
        buffer := buffer + c.out
    end

    append_string (s: STRING)
    -- Добавляет строку в конец.
    local
        old_count: INTEGER
    do
        old_count := buffer.count
        buffer := buffer + s
    end

    append_integer (i: INTEGER)
	-- Добавляет целое число в конец.
    local
        copy_i, j: INTEGER
        digits: ARRAY [INTEGER]
	do
        -- Добавляем минус в начале, если число отрицательное.
		if i < 0 then
            append_string ("-")
        end

        -- Переворачиваем переданное число.
        create digits.with_capacity (1, 1)
        copy_i := i
        from until copy_i = 0 loop
            digit := copy_i \\ 10
            digits.add_last(digit)
            copy_i := copy_i // 10
        end

        -- Добавляем цифры в обратном порядке.
        from
            j := digits.upper
        until
            j < digit.upper
        loop
            append_string (digits [i].out)
            j := j - 1
        end
	end

feature

    to_string: STRING
    -- Неизменяемая копия содержимого буффера.
    do
        Result := buffer.out
    end

end