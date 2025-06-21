class
    HASH_TABLE [V, K -> HASHABLE]
    -- Хэш-таблица. Хранит пары "ключ-значение".

create
    make,
    empty

feature {NONE}

    keys: ARRAY [K]
    -- Ключи.

    values: ARRAY [V]
    -- Значения.

    occupied: ARRAY [BOOLEAN]
    -- Какие ячейки являются занятыми.

    Default_capacity: INTEGER = 17
    -- Размер хэш-таблицы по умолчанию.

feature
-- Конструкторы.

    make (a_capacity: INTEGER)
    -- Создает хэш-таблицу с заданной начальной емкостью.
    -- @param size Начальный размер хэш-таблицы.
    do
        capacity := a_capacity
        create keys.with_capacity (capacity, 1)
        create values.with_capacity (capacity, 1)
        create occupied.make_filled (False, keys.lower, keys.upper)
    end

    empty
    -- Создает "пустую" хэш-таблицу.
    do
        make (Default_capacity)
    end

feature

    current_keys: like keys
    -- Ключи, записанные в хэш-таблицу.
    -- @return Новый массив ключей, записанных в хэш-таблицу.
    local
        i, j: INTEGER
        ks: like keys
    do
        create ks.with_capacity (count, 1)

        from
            i := 1
            j := 1
        until
            i > keys.count
        loop
            if occupied [i] then
                ks [j] := keys [i]
                j := j + 1
            end

            i := i + 1
        end

        Result := ks
    end

    count: INTEGER
    -- Возвращает количество пар ключ-значение в хэш-таблице.
    -- @return Количество пар ключ-значение в хэш-таблице.
    local
        i: INTEGER
    do
        from
            i := occupied.lower
        until
            i > occupied.upper
        loop
            if occupied [i] then Result := Result + 1 end
            i := i + 1
        end
    end

    capacity: INTEGER
    -- Сколько всего может быть элементов в хэш-таблице.

    is_full: BOOLEAN
    -- Заполнена ли хэш-таблица полностью?
    -- @return True, если в таблице нет свободных ячеек, иначе - False.
    then
        count = occupied.count
    end

    is_empty: BOOLEAN
    -- Пустая ли хэш-таблица?
    -- @return True, если в таблице ничего нет, иначе - False.
    then
        count = 0
    end

feature
-- Получение элементов хэш-таблицы.

    item (k: K): V
    -- Получить элемент по ключу `k`.
    -- @param k Ключ.
    -- @return Значение по ключу.
    local
        i: INTEGER
        cached_found: BOOLEAN
        cached_found_item: V
    do
        -- Сохраняем старые значения `found` и `found_item`,
        -- т.к. далее для поиска используем мутатор `search`.
        cached_found := found
        cached_found_item := found_item 

        search (k)

        require_that (
            found,
            "Key " + k.out + "is not present in the hash table"
        )

        Result := found_item

        -- Восстаналиваем сохраненные ранее значения.
        found := cached_found
        found_item := cached_found_item
    end

feature
-- Помещение новых элементов в хэш-таблицу.

    put_only_new (v: like item; k: K)
    -- Помещает элемент `v` по ключу `k`, если его не было ранее.
    -- Если он уже был внутри, ничего не делает.
    -- @param `v` Значение.
    -- @param `k` Ключ.
    do
        if not has_key (k) then
            put (v, k)
        end
    end

    replace (v: like item; k: K)
    -- Заменяет элемент `v` по ключу `k`, если он уже был записан.
    -- Если такого ключа не было, ничего не делает.
    -- @param `v` Значение.
    -- @param `k` Ключ.
    do
        if has_key (k) then
            put (v, k)
        end
    end

    force (v: like item; k: K)
    -- Помещает элемент `v` по ключу `k`.
    -- Если элемент с ключем `k` уже есть, заменяет его.
    -- Синоним к `put` в данной реализации.
    -- @param `v` Значение.
    -- @param `k` Ключ.
    do
        put (v, k)
    end

    extend (v: like item; k: K)
    -- Помещает элемент `v` по ключу `k`.
    -- Если элемент с ключем `k` уже есть, заменяет его.
    -- Синоним к `put` в данной реализации.
    -- @param `v` Значение.
    -- @param `k` Ключ.
    do
        put (v, k)
    end

    put (v: like item; k: K)
    -- Помещает элемент `v` по ключу `k`.
    -- Если элемент с ключем `k` уже есть, заменяет его.
    -- @param `v` Значение.
    -- @param `k` Ключ.
    local
        i: INTEGER
    do
        if is_full then accomodate end

        -- Производим поиск в правой половине массиве:
        -- начиная с предположительного индекса и до конца.
        from
            i := internal_index (k)
        until
            (i > keys.upper) or else (not occupied [i] or occupied [i] and then keys [i] = k)
        loop
            i := i + 1
        end

        -- Если свободная ячейка не была найдена, ищем
        -- её в левой половине массива.
        if i > keys.upper then
            from
                i := keys.lower
            until
                (i > keys.upper) or else (not occupied [i] or occupied [i] and then keys [i] = k)
            loop
                i := i + 1
            end
        end

        -- Записываем элемент во внутренний массив.
        keys [i] := k
        values [i] := v
        occupied [i] := True
    end

feature
-- Удаление элементов.

    remove (k: K)
    -- Удаляет элемент по ключу `k` из таблицы.
    -- Если такого элемента нет, то ничего не делает.
    -- @param k Ключ элемента для удаления.
    local
        i: INTEGER
    do
        i := find_index_of (k)

        if i /= 0 then
            keys [i] := Void
            values [i] := Void
            occupied [i] := False
        end
    end

feature
-- Проверки вхождения элементов.

    found_item: V
    -- Элемент, найденный в результате вызова `has_key`.
    -- `Void`, если элемент не был найден.

    found: BOOLEAN
    -- Был ли найден элемент в результате вызова `search`?

    search (k: K)
    -- Выполняет поиск ключа `k` в таблице.
    -- Устанавливает `has_found` и `found_item` для более быстрого поиска.
    -- @param k Ключ для поиска.
    local
        i: INTEGER
    do
        i := find_index_of (k)

        if i /= 0 then
            found := True
            found_item := values [i]
        else
            found := False
            found_item := Void
        end
    end

    has, has_key (k: K): BOOLEAN
    -- Есть ли переданный ключ в хэш-таблице?
    -- @param k Ключ для поиска.
    -- @return `True`, если ключ `k` есть в таблице, иначе - `False`.
    then
        find_index_of (k) /= 0
    end

    has_value (v: like item): BOOLEAN
    -- Есть ли переданное значение в массиве?
    local
        i: INTEGER
    do
        from
            i := values.lower
        until
            (i > values.upper) or else Result
        loop
            Result := occupied [i] and then values [i] = v
            i := i + 1
        end
    end

feature {NONE}
-- Реализация.

    internal_index (k: K): INTEGER
    -- Индекс во внутреннем хранилище.
    then
        k.hash_code \\ keys.count + 1  
    end

    accomodate
    -- Выделяет новую память для внутреннего массива.
    -- Размер новой емкость: `cap := `(old cap) * 1.5`.
    local
        l_capacity: INTEGER
        l_keys: ARRAY [K]
        l_values: ARRAY [V]
        l_occupied: ARRAY [BOOLEAN]
        i: INTEGER
    do
        l_capacity := (capacity * 15 // 10)
        create l_keys.with_capacity (l_capacity, 1)
        create l_values.with_capacity (l_capacity, 1)
        create l_occupied.make_filled (False, keys.lower, keys.upper)

        from
            i := keys.lower
        until
            i = keys.upper
        loop
            l_keys [i] := keys [i]
            l_values [i] := values [i]
            l_occupied [i] := occupied [i]
        end

        capacity := l_capacity
        keys := l_keys
        values := l_values
        occupied := l_occupied
    end

    find_index_of (k: K): INTEGER
    -- Есть ли переданный ключ в хэш-таблице?
    -- @param `k` Ключ для поиска.
    -- @return `True`, если ключ `k` есть в таблице, иначе - `False`.
    local
        possible_index: INTEGER
        l_found: BOOLEAN
        i: INTEGER
    do
        possible_index := internal_index (k)

        -- Производим поиск в правой половине массиве:
        -- начиная с possible_index и до конца.
        from
            i := possible_index
        until
            (i > keys.upper) or else l_found
        loop
            l_found := occupied [i] and then keys [i] = k
            i := i + 1
        end

        -- Если в правой половине массива такого элемента не было найдено,
        -- пробуем искать его в левой.
        if not l_found then
            from
                i := keys.lower
            until
                i = possible_index or else l_found
            loop
                l_found := occupied [i] and then keys [i] = k
                i := i + 1
            end
        end

        -- Вычитаем -1 из `i`, т.к. `i` указывает на следующую ячейку
        -- (см. цикл выше).
        if l_found then Result := i - 1 end
    end

end
