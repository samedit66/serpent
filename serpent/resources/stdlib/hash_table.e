class
    HASH_TABLE [K -> HASHABLE, V]
    -- Хэш-таблица, которая хранит пары ключ-значение.

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

    make (a_capacity: INTEGER)
    -- Создает хэш-таблицу с заданным размером.
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
    then
        count = occupied.count
    end

    is_empty: BOOLEAN
    -- Пустая ли хэш-таблица?
    then
        count = 0
    end

feature

    at, item (k: K): V
    -- Получить элемент по ключу `k`.
    -- @param k Ключ.
    -- @return Значение по ключу.
    local
        i: INTEGER
    do
        i := index_of (k)
        require_that (i /= 0, "Key " + k.out + "is not present in the hash table")
        Result := values [i]
    end

feature

    put (v: like item; k: K)
    local
        i: INTEGER
    do
        if is_full then rehash end

        i := internal_index (k)
        from until not occupied [i]
        loop i := i + 1 end

        keys [i] := k
        values [i] := v
        occupied [i] := True
    end

feature {NONE}

    rehash
    -- Выполняет "рехэш" хэш-таблицы:
    -- увеличивает емкость в 1.5 раза и копирует все элементы
    -- в новую область памяти.
    local
        l_capacity: INTEGER
        l_keys: ARRAY [K]
        l_values: ARRAY [V]
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

feature

    has_key (k: like item): BOOLEAN
    then
        index_of (k) /= 0
    end

    has_value (v: V): BOOLEAN
    local
        i: INTEGER
    do
        from
            i := values.lower
        until
            (i > values.upper) or else Result
        loop
            Result := values [i] = v
            i := i + 1
        end
    end

feature {NONE}

    index_of (k: like item): INTEGER
    local
        seen_elements_count: INTEGER
    do
        seen_elements_count := 1

        from
            Result := internal_index (k)
        until
            (seen_elements_count = count) or else (keys [i] = k)
        loop
            Result := Result + 1
            seen_elements_count := seen_elements_count + 1
        end

        if Result > keys.upper then Result := 0 end
    end

    internal_index (k: like item): INTEGER
    then
        k.hash_code % keys.count + 1  
    end

end