class
    ARRAY [G]
-- Динамический массив. Обертка над ArrayList в Java.

create
    make_filled

feature
-- Конструкторы массива.

    make_filled (fill_value: G; min_index, max_index: INTEGER)
    -- Создает массив с заданным промежутком индексов [`min_index`..`max_index`]
    -- и заполняет его значением `fill_value`.
    do
        if min_index > max_index then
            crash_with_message ("min_index cannot be greater than max_index")
        end

        lower := min_index
        upper := max_index
        initialize (count, fill_value)
    end

feature
-- Доступ к элементам массива.

    item (index: INTEGER): G
    -- Возвращает элемент под индексом index.
    do
        check_index (index)

        Result := item_raw (map_index (index))
    end

feature
-- Изменение элементов массива.

    put (element: G; index: INTEGER)
    -- Помещает в массив элемент element по индексу index.
    do
        check_index (index)

        put_raw (element, map_index (index))
    end

    swap (i1, i2: INTEGER)
    -- Обменивает местами элементы под индексами `i1` и `i2`.
    local
        temp: G
    do
        check_index (i1)
        check_index (i2)

        temp := item (i1)
        put (item (i2), i1)
        put (temp, i2)
    end

feature
-- Характеристики массива.

    lower: INTEGER
    -- Нижний допустимый индекс массива.

    upper: INTEGER
    -- Верхний допустимый индекс массива.

    count: INTEGER
    -- Возвращает количество элементов в массиве.
    then upper - lower + 1 end

    empty: BOOLEAN
    -- Проверяет, является ли массив пустым.
    then count = 0 end

feature
-- Проверки.

    valid_index (index: INTEGER): BOOLEAN
    -- Проверяет, допустимый ли это индекс для массива
    then lower <= index and then index <= upper end

feature {NONE}
-- Все что связано с индексом в массиве.

    map_index (index: INTEGER): INTEGER
    -- Преобразует индекс массива из промежутка [lower..upper]
    -- в "настоящий" индекс из промежутка [0..upper-lower]
    then index - lower end

    check_index (index: INTEGER)
    -- Проверяет, является ли индекс `index` допустимым,
    -- если нет прекращает выполнение программы с выводом диагностического сообщения.
    do
        if not valid_index (index) then
            crash_with_message (index.to_string + " not a valid index")
        end
    end

feature {NONE}
-- Низкоуровневые функции взаимодействия с массивом.

    initialize (a_count: INTEGER; value: ANY)
        -- Выполняет инициализацию массива заданного размера `a_count`,
        -- задавая всем элементам значение `value`.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_initialize"
    end

    item_raw (index: INTEGER): NONE
        -- Возвращает элемент по индексу `index`.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_item_raw"
    end

    put_raw (element: ANY; index: INTEGER)
        -- Помещает значение `element` в массив по индексу `index`.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_put_raw"
    end    
end
