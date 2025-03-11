class
    APPLICATION
                    
inherit
    IO
    QUICK_SORTER
                                 
feature

    make
        local
            a: ARRAY [INTEGER]
        do
            -- Создаём массив с начальными значениями
            create a.with_capacity (10, 1)
            a.put (34, 1)
            a.put (7, 2)
            a.put (23, 3)
            a.put (32, 4)
            a.put (5, 5)
            a.put (62, 6)
            a.put (31, 7)
            a.put (4, 8)
            a.put (45, 9)
            a.put (16, 10)
            
            print ("Исходный массив: ")
            print_array (a)
            
            quick_sort (a, a.lower, a.upper)
            
            print ("Отсортированный массив: ")
            print_array (a)
        end

feature

    print_array (a: ARRAY [INTEGER])
            -- Выводит элементы массива в консоль.
        local
            i: INTEGER
        do
            from
                i := a.lower
            until
                i > a.upper
            loop
                print (a.item(i))
                print (" ")
                i := i + 1
            end
            new_line
        end
end
