class
    ARRAY [G]
-- Динамический массив. Обертка над ArrayList в Java.

create
    make_filled_with

feature
-- Конструкторы массива.

    make_filled_with (a_lower, a_upper: INTEGER; value: G)
    -- Создает массив с заданным промежутком индексов [a_lower..a_upper]
    -- и заполняет его значением value.
    do
        lower := a_lower
        upper := a_upper
        raw_array := make_filled_with_raw (count, value)
    end

feature {NONE}
-- Непосредственное создание массива.

    make_filled_with_raw(cap: INTEGER; value: ANY): NONE
    -- Непосредственно создает массив.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_make_filled_with_raw"
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
    then
        upper - lower + 1
    end

feature
-- Проверки.

    valid_index (index: INTEGER): BOOLEAN
    -- Проверяет, допустимый ли это индекс для массива
    then
        lower <= index and then index <= upper
    end

feature {NONE}
-- Все что связано с индексом в массиве.

    map_index (index: INTEGER): INTEGER
    -- Преобразует индекс массива из промежутка [lower..upper]
    -- в "настоящий" индекс из промежутка [0..upper-lower]
    then
        index - lower
    end

feature {NONE}
-- Доступ к "сырому" массиву.
    raw_array: NONE

    item_raw (index: INTEGER): NONE
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_item_raw"
    end

    put_raw (element: ANY; index: INTEGER)
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_put_raw"
    end
end
