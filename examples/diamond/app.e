class
    APPLICATION
                    
inherit
    IO
                                 
feature
            
    make
    local
        arr: ARRAY [BASE]
        d1: DERIVED1
        d2: DERIVED2
        d: DIAMOND
        i: INTEGER
    do
        create arr.with_capacity (4, 1)

        arr[1] := create {BASE}.make

        create d1.make
        arr[2] := d1

        create d2.make
        arr[3] := d2

        create d.make
        arr[4] := d

        from
            i := arr.lower
        until
            i > arr.upper
        loop
            arr[i].print_origin
            i := i + 1
        end
    end
end

class
    BASE

inherit
    IO
    EQ

create
    make

feature
    make
        do
        end

    print_origin
        do
            println ("Called from BASE")
            new_line
        end

    non_redefined_anywhere
        do
            println ("Is is not redefined anywhere")
        end

    redefined_by_DERIVED1
        do
            println ("Should be redefined by DERIVED1")
        end

    redefined_by_DERIVED2
        do
            println ("Should be redefined by DERIVED2")
        end

    is_equal (other: like Current): BOOLEAN
        then True end
end

class
    DERIVED1

inherit
    IO
    BASE
    redefine
        make,
        print_origin,
        redefined_by_DERIVED1
    end

create
    make

feature
    make
        do
        end

    print_origin
        do
            println ("Called from DERIVED1")
            println ("Calling precursor of print_origin in DERIVED1")
            Precursor
            new_line
        end

    redefined_by_DERIVED1
        do
            println ("Is redefined by DERIVED1")
        end
end

class
    DERIVED2

inherit
    IO
    BASE
    redefine
        make,
        print_origin,
        redefined_by_DERIVED2
    end

create
    make

feature
    make
    do
    end

    print_origin
    do
        println ("Called from DERIVED2")
        println ("Calling precursor of print_origin in DERIVED2")
        Precursor
        new_line
    end

    redefined_by_DERIVED2
    do
        println ("Is redefined by DERIVED2")
    end
end

class
    DIAMOND

inherit
    IO
    DERIVED1
        redefine
            make,
            print_origin
        select redefined_by_DERIVED1
        end
    DERIVED2
        redefine
            make,
            print_origin
        select redefined_by_DERIVED2
        end

create
    make

feature
    make
        do
        end

    print_origin
        do
            println ("Called from DIAMOND (diamond inheritance)")
            println ("Calling both variants of print_origin in DIAMOND")
            {DERIVED1} Precursor
            {DERIVED2} Precursor
            new_line
        end
end
