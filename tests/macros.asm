; macros — проверка #define: подстановка макросов в мнемонику и операнды
#define OUT     1
#define CH_A    65
#define CH_B    66
.text
        LDIM CH_A
        WR OUT
        LDIM CH_B
        WR OUT
        HLT
