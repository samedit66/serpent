class
    ARRAY [G]
-- Динамический массив. Обертка над ArrayList в Java.

feature

    make_filled_with (a_lower, a_upper: INTEGER; value: G)
    local
        i: INTEGER
    do
        make_raw (a_low, a_high)

        lower := a_lower
        upper := a_upper

        from i := lower until i = upper loop
            put (value, i)
        end
    end

feature
-- Доступ к элементам массива.

    item (index: INTEGER): G
    -- Возвращает элемент под индексом index.
    then
        item_raw (map_index (index))
    end

feature
-- Устаналивает значение элементу массива по индексу index.

    put (element: G; index: INTEGER)
    -- Помещает в массив элемент element по индексу index.
    do
        put_raw (element, map_index (index))
    end

feature
-- Характеристики массива.

    lower: INTEGER
    -- Нижний допустим индекс массива.

    upper: INTEGER
    -- Верхний допустимый индекс массива.

    count: INTEGER
    -- Возвращает количество элементов в массиве.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_count"
    end

feature {NONE}

    map_index (index: INTEGER): INTEGER
    then
        index - lower
    end

    item_raw (index: INTEGER): NONE
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_item_raw"
    end

    put_raw (element: G; index: INTEGER)
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_item_raw"
    end
end
