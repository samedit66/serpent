class
    APPLICATION
-- Определяет n-ное число Фибоначчи.

inherit
    IO

feature

    make
        local
            n, a, b, i, temp: INTEGER
        do
            print ("Введите n: ")
            read_integer
            n := last_integer

            println (n)

            if n < 0 then
                println ("Некорректное значение: n должно быть неотрицательным")
            elseif n = 0 then
                println ("Fibonacci(0) = 0")
            elseif n = 1 then
                println ("Fibonacci(1) = 1")
            else
                a := 0
                b := 1
                from
                    i := 2
                until
                    i > n
                loop
                    temp := a + b
                    a := b
                    b := temp
                    i := i + 1
                end
                println ("Fibonacci(" + n.out + ") = " + b.out)
            end
        end

end
