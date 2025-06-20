class
    ARRAY_SORTER [T -> COMPARABLE]

feature

    sort (a: ARRAY [T])
    -- Выполняет сортировку массива `a` по месту.
    -- Использует алгоритм быстрой сортировки.
    do
        quick_sort (a, a.lower, a.upper)
    end

feature

    quick_sort (a: ARRAY [T]; low, high: INTEGER)
    -- Сортирует подмассив a[low..high] методом быстрой сортировки.
    local
        i, j, temp: INTEGER
        pivot: T
    do
        if low < high then
            i := low
            j := high
            pivot := a.item ((low + high) // 2)
            from
            until i > j
            loop
                from
                until a.item(i) >= pivot
                loop
                    i := i + 1
                end
                from
                until a.item(j) <= pivot
                loop
                    j := j - 1
                end
                if i <= j then
                    -- Меняем местами элементы a[i] и a[j]
                    a.swap (i, j)
                    i := i + 1
                    j := j - 1
                end
            end
            quick_sort (a, low, j)
            quick_sort (a, i, high)
        end
    end
    
end
