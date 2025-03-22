class
    DIAMOND

inherit
    DERIVED1
        redefine
            print_origin
        select
            redefined_by_DERIVED1
        end
    DERIVED2
        redefine
            print_origin
        select
            redefined_by_DERIVED2
        end

feature

    print_origin
        do
            io.put_string ("Called from DIAMOND (diamond inheritance)")
            io.new_line

            io.put_string ("Calling both variants of print_origin in DIAMOND")
            io.new_line

            {DERIVED1} Precursor
            {DERIVED2} Precursor

            io.put_string ("End calling both variants of print_origin in DIAMOND")
            io.new_line
        end
end
