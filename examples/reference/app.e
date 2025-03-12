class
    APPLICATION

inherit
    IO

create
    make

feature

    make
        local
            a: ARRAY[INTEGER]
            t: INTEGER
            k: STRING
            tt: T
        do
            create a.with_capacity (4, 0)
            a[0] := 1
            a[1] := 2
            a[2] := 3
            a[3] := 4

            t := 5
            k := "abb"
            create tt.make

            print_array (a)
            print (t.out + "%N")
            print (tt.k.out + "%N")
            print (k + "%N")

            println ("BEFORE CALLING TO REF TEST%N")

            ref_test (a, t, tt, k)

            print ("AFTER CALLING TO REF TEST%N")
            print_array (a)
            print (t.out + "%N")
            print (tt.k.out + "%N")
            print (k + "%N")
        end

    print_array (a: ARRAY[INTEGER])
        local
            i: INTEGER
        do
            from
                i := a.lower
            until
                i > a.upper
            loop
                print (a[i].out + " ")
                i := i + 1
            end
            new_line
        end


    ref_test (a: ARRAY[INTEGER]; t: INTEGER; tt: T; k: STRING)
    do
        println ("START REF TEST")

        a[1] := 5
        -- create a.with_capacity (3, 0)
        a[0] := 5
        a[1] := 6
        a[2] := 7

        -- t := 7
        -- k := "gfgfg"
        tt.set_k (10)
        -- create tt.make

        print_array (a)
        println (tt.k)

        println ("END REF TEST")
    end
end

class
    T

create
    make

feature
    make
    do
        k := 5
    end

feature
    k: INTEGER

    set_k (new_k: INTEGER)
    do
        k := new_k
    end
end
