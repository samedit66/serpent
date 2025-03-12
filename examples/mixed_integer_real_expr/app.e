class
    APPLICATION

inherit
    IO

create
    make

feature

    make
            -- Точка входа в программу.
        local
            int_number: INTEGER
            float_number: REAL
        do
            int_number := 10
            float_number := 3.5

            -- Арифметические операции (смешанные типы: INTEGER и REAL)
            println ("Арифметические операции:")
            println ("Сложение: " + int_number.out + " + " + float_number.out + " = " + ((int_number + float_number).out))
            println ("Вычитание: " + int_number.out + " - " + float_number.out + " = " + ((int_number - float_number).out))
            println ("Умножение: " + int_number.out + " * " + float_number.out + " = " + ((int_number * float_number).out))
            println ("Деление: " + int_number.out + " / " + float_number.out + " = " + ((int_number / float_number).out))

            -- Арифметические операции (только INTEGER)
            println ("Арифметические операции:")
            println ("Сложение: " + int_number.out + " + " + int_number.out + " = " + ((int_number + int_number).out))
            println ("Вычитание: " + int_number.out + " - " + int_number.out + " = " + ((int_number - int_number).out))
            println ("Умножение: " + int_number.out + " * " + int_number.out + " = " + ((int_number * int_number).out))
            println ("Деление: " + int_number.out + " / " + (int_number + 5).out + " = " + ((int_number / (int_number + 5)).out))

            -- Арифметические операции (REAL и INTEGER, INTEGER приводится к REAL)
            println ("Арифметические операции:")
            println ("Сложение: " + float_number.out + " + " + int_number.out + " = " + ((float_number + int_number).out))
            println ("Вычитание: " + float_number.out + " - " + int_number.out + " = " + ((float_number - int_number).out))
            println ("Умножение: " + float_number.out + " * " + int_number.out + " = " + ((float_number * int_number).out))
            println ("Деление: " + float_number.out + " / " + int_number.out + " = " + ((float_number / int_number).out))

            -- Арифметические операции (только REAL)
            println ("Арифметические операции:")
            println ("Сложение: " + float_number.out + " + " + float_number.out + " = " + ((float_number + float_number).out))
            println ("Вычитание: " + float_number.out + " - " + float_number.out + " = " + ((float_number - float_number).out))
            println ("Умножение: " + float_number.out + " * " + float_number.out + " = " + ((float_number * float_number).out))
            println ("Деление: " + float_number.out + " / " + float_number.out + " = " + ((float_number / float_number).out))

            -- Целочисленное деление и остаток от деления (для INTEGER)
            println ("Целочисленное деление: " + int_number.out + " div 3 = " + ((int_number // 3).out))
            println ("Остаток от деления: " + int_number.out + " mod 3 = " + ((int_number \\ 3).out))

            -- Сравнение чисел (INTEGER приводится к REAL)
            println ("Сравнение чисел:")
            println (int_number.out + " > " + float_number.out + ": " + ((int_number > float_number).out))
            println (int_number.out + " < " + float_number.out + ": " + ((int_number < float_number).out))
            println (int_number.out + " = " + float_number.out + ": " + ((int_number = float_number).out))

            -- Сравнение чисел (REAL с REAL)
            println ("Сравнение чисел:")
            println (float_number.out + " > " + float_number.out + ": " + ((float_number > float_number).out))
            println (float_number.out + " < " + float_number.out + ": " + ((float_number < float_number).out))
            println (float_number.out + " = " + float_number.out + ": " + ((float_number = float_number).out))

            -- Сравнение чисел (INTEGER с INTEGER)
            println ("Сравнение чисел:")
            println (int_number.out + " > " + int_number.out + ": " + ((int_number > int_number).out))
            println (int_number.out + " < " + int_number.out + ": " + ((int_number < int_number).out))
            println (int_number.out + " = " + int_number.out + ": " + ((int_number = int_number).out))

            -- Сравнение чисел (REAL и INTEGER)
            println ("Сравнение чисел:")
            println (float_number.out + " > " + int_number.out + ": " + ((float_number > int_number).out))
            println (float_number.out + " < " + int_number.out + ": " + ((float_number < int_number).out))
            println (float_number.out + " = " + int_number.out + ": " + ((float_number = int_number).out))
        end
end
