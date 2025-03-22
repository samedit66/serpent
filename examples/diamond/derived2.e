class
    DERIVED2

inherit
    BASE
    redefine
        print_origin,
        redefined_by_DERIVED2
    end

feature

    print_origin
    do
        io.put_string ("Called from DERIVED2")
        io.new_line

        io.put_string ("Calling precursor of print_origin in DERIVED2")
        io.new_line

        Precursor

        io.put_string ("End calling precursor of print_origin in DERIVED2")
        io.new_line
    end

    redefined_by_DERIVED2
    do
        io.put_string ("Is redefined by DERIVED2")
        io.new_line

        io.put_string ("Calling precursor of redefined_by_DERIVED2 in DERIVED2")
        io.new_line

        Precursor

        io.put_string ("End calling precursor of redefined_by_DERIVED2 in DERIVED2")
        io.new_line
    end
end
