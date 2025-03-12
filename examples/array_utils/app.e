class
    APPLICATION
                    
inherit
    IO
    QUICK_SORTER
                                 
feature

    make
        local
            a: ARRAY [INTEGER]
            size: INTEGER
            i: INTEGER
        do
            -- Создаём массив с начальными значениями
            print ("input array size: ")
            read_integer

            create a.with_capacity (last_integer, 1)
            from i := 1 until i > a.count loop
                print ("> ")
                read_integer
                a.put (last_integer, i)
                i := i + 1
            end

            print ("Исходный массив: ")
            print_array (a)
            
            a.bubble_sort
            
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
