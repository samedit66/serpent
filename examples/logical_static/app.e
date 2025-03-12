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
            x, y, z, a, b, c, d, e: BOOLEAN
        do
            println ("Testing: True OrElse False")
            x := left_true_test or else right_false_test

            println ("Testing: False OrElse False")
            y := left_false_test or else right_false_test

            println ("Testing: False AndThen False")
            z := left_false_test and then right_false_test

            println ("Testing: True AndThen False")
            a := left_true_test and then right_false_test

            println ("Testing: True Or False")
            b := left_true_test or right_false_test

            println ("Testing: False Or False")
            c := left_false_test or right_false_test

            println ("Testing: False And False")
            d := left_false_test and right_false_test

            println ("Testing: True And False")
            e := left_true_test and right_false_test
        end

    left_false_test: BOOLEAN
        do
            println ("left = false evaluated")
            Result := False
        end

    right_false_test: BOOLEAN
        do
            println ("right = false evaluated")
            Result := False
        end

    left_true_test: BOOLEAN
        do
            println ("left = true evaluated")
            Result := True
        end

    right_true_test: BOOLEAN
        do
            println ("right = true evaluated")
            Result := True
        end
end
