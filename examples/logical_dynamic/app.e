class
    APPLICATION

inherit
    IO

create
    make

feature

    make
    local
        x, y, z, a, b, c, d, e: BOOLEAN
    do
        println ("Testing or else%N")
        x := left_test or else right_test

        println ("Testing and then%N")
        z := left_test and then right_test

        println ("Testing or %N")
        b := left_test or right_test

        println ("Testing and%N")
        e := left_test and right_test
    end

    left_test: BOOLEAN
    local
        input_value: INTEGER
    do
        println ("Введите значение для Left (True/False): ")
        read_integer
        Result := last_integer < 10
        println ("Left = " + Result.out + " evaluated")
    end

    right_test: BOOLEAN
    local
        input_value: INTEGER
    do
        println ("Введите значение для Right (True/False): ")
        read_integer
        Result := last_integer > 20
        println ("Right = " + Result.out + " evaluated")
    end

end