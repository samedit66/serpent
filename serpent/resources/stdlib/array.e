class
    ARRAY [G -> COMPARABLE]
-- Динамический массив. Обертка над ArrayList в Java.
-- В качестве элемента массива может быть любой тип,
-- значения которого можно сравнивать.

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
-- Поиск элементов в массиве.

    index_of (element: like item): INTEGER
    -- Возвращает индекс элемента `element` в массиве.
    -- В случае, если этого элемента нет в массиве, возвращается `upper + 1`.
    local
        i: INTEGER
        found: BOOLEAN
    do
        Result := upper + 1

        from
            i := lower
        until
            i <= upper or found
        loop
            if element = item (i) then
                Result := i
                found := True
            end

            i := i + 1
        end
    end

    has (element: like item): BOOLEAN
    -- Проверяет, есть ли элемент `element` в массиве.
    then index_of (element) /= upper + 1 end

feature
-- Добавление элементов в массив.

    add_first (element: like item)
    -- Добавляет элемент в начало массива.
    do
        add (element, lower)
    end

    add_last (element: like item)
    -- Добавляет элемент в конец массива.
    do
        add (element, upper + 1)
    end

    insert, add (element: like item; index: INTEGER)
    -- Добавляет элемент в массив по заданному индексу,
    -- возможно, выполняя сдвиг элементов.
    do
        if index < lower or else index > upper + 1 then
            crash_with_message (index.to_string + " not a valid index")
        end

        add_raw (element, map_index (index))
        upper := upper + 1
    end

feature
-- Удаление элементов из массива.

    remove_first
    -- Удаляет первый элемент из массива.
    do
        remove (lower)
    end

    remove_last
    -- Удаляет последний элемент из массива.
    do
        remove (upper)
    end

    remove (index: INTEGER)
    -- Удаляет элемент из массива по индексу `index`.
    do
        check_index (index)

        remove_raw (map_index (index))
        upper := upper - 1
    end

feature
-- Изменение элементов массива.

    put (element: like item; index: INTEGER)
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

    bubble_sort
    -- Выполняет сортировку массива методом пузырька.
    local
        i, j: INTEGER
    do
        from
            i := lower
        until
            i > upper
        loop
            from
                j := i
            until
                j > upper
            loop
                if item (i) > item (j) then
                    swap (i, j)
                end

                j := j + 1
            end

            i := i + 1
        end
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
    -- Проверяет, допустимый ли это индекс для массива.
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
    -- Заменяет значение по индексу `index` на `element`.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_put_raw"
    end

    add_raw (element: ANY; index: INTEGER)
    -- Помещает значение `element` по заданному индексу в массив,
    -- выполняя смещение всех элементов справа на 1.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_add_raw"
    end

    remove_raw (index: INTEGER)
        -- Удаляет элемент по индексу `index`.
        external "Java"
        alias "com.eiffel.PLATFORM.ARRAY_remove_raw"
    end
end
