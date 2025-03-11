class
    APPLICATION
                    
inherit
    IO
                                 
feature
                    
    make
    local n: INTEGER
    do
        print ("Введите число: ")
        read_integer
        n := last_integer

        println ("Факториал через рекурсию: " + rec_factorial (n).out)
        println ("Факториал через цикл: " + iter_factorial (n).out)
    end

    rec_factorial (n: INTEGER): INTEGER
    local status: BOOLEAN
    do
        if n = 0 or else n = 1 then
            Result := 1
        else
            Result := n * rec_factorial (n-1)
        end
    end

    iter_factorial (n: INTEGER): INTEGER
    do
        Result := 1

        from until n = 0 loop
            Result := Result * n
            n := n - 1
        end
    end
end
