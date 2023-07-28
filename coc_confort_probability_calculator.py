import argparse

parser = argparse.ArgumentParser(
    "This program can calculate the probability of results in coc conforting under 7th edition rule."
)
parser.add_argument("-a",
                    default=None,
                    type=int,
                    help="The success rate of A side.")
parser.add_argument("-b",
                    default=None,
                    type=int,
                    help="The success rate of B side.")
parser.add_argument("--fascio",
                    "-f",
                    default=100,
                    type=int,
                    help="The lower bound of fascio.")
parser.add_argument("--great",
                    "-g",
                    default=1,
                    type=int,
                    help="The higher bound of great success.")
args = parser.parse_args()

if args.a is None:
    args.a = int(input("The success rate of A side (0-100) is:"))
if args.b is None:
    args.b = int(input("The success rate of B side (0-100) is:"))


def succ_rates(rate):
    return [
        max(0, args.great),
        max(0,
            int(rate / 5) - args.great),
        max(0,
            int(rate / 2) - int(rate / 5)),
        max(0, rate - int(rate / 2)),
        max(0, args.fascio - rate - 1),
        max(0, 100 - args.fascio + 1)
    ]


a_succ_rates = succ_rates(args.a)
b_succ_rates = succ_rates(args.b)

# m[i,j]=a[i]*b[j]
succ_rate_mat = [[a_succ_rates[i] * b_succ_rates[j] for j in range(6)]
                 for i in range(6)]
'''
    b0  b1  b4  b5
a0  gg  gc  gf  gF
a1  cg  cc  cf  cF
a4  fg  fc  ff  fF
a5  Fg  Fc  Ff  FF
'''

both_success_rate = args.a * args.b
both_fail_rate = (100 - args.a) * (100 - args.b)

same_success_rate = sum([succ_rate_mat[i][i] for i in range(4)])
same_fail_rate = succ_rate_mat[4][4] + succ_rate_mat[5][5]

a_win_rate = sum(
    [sum([succ_rate_mat[i][j] for j in range(i + 1, 6)]) for i in range(0, 5)])
b_win_rate = sum(
    [sum([succ_rate_mat[i][j] for j in range(0, i)]) for i in range(1, 6)])

print(
    f"""The probability of both success at same degree is 0.{same_success_rate:0>4};
The probability of both fail at same degree is 0.{same_fail_rate:0>4};
The probability of A/B side have higher degree is 0.{a_win_rate:0>4}/0.{b_win_rate:0>4};
The probabilty of A/B side have higher or equal degree is 0.{(a_win_rate+same_fail_rate+same_success_rate):0>4}/0.{(b_win_rate+same_fail_rate+same_success_rate):0>4}"""
)
