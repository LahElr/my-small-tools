import argparse
import math

parser = argparse.ArgumentParser(
    "This program calculates the overall sucess rate of penlty dices or bonus dices in coc.")
parser.add_argument("-o", "--original", required=True,
                    help="The original sucess rate.", type=int)
parser.add_argument("-p", "--penlty", action="store_true",
                    help="Is it penlty?")
parser.add_argument("-b", "--bonus", action="store_true", help="Is it bonus?")
parser.add_argument("-c", "--count", type=int,
                    help="The count of penlty or bonus.")
args = parser.parse_args()

if args.count < 0:
    raise ValueError("You can not give extra dices of minus count!")
if args.original < 0:
    raise ValueError("You can not have a sucess rate lower than 0!")


def calculate(original, status, count):
    if count == 0:
        return original
    if original == 0:
        return 0
    if status == "p":
        ten_unit = original//10
        one_unit = original % 10

        ten_unit_dice_count = 1+count

        ten_unit_dice_probability_ = [
            ((n+1)/10)**ten_unit_dice_count for n in range(10)]
        ten_unit_dice_probability = [
            0.1**ten_unit_dice_count, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(1, 10):
            ten_unit_dice_probability[i] = ten_unit_dice_probability_[
                i]-ten_unit_dice_probability_[i-1]
        del ten_unit_dice_probability_
        ten_unit_dice_no_0_probability = [(k**ten_unit_dice_count-(
            k-1)**ten_unit_dice_count if k >= 1 else 0)/10**ten_unit_dice_count for k in range(10)]
        ten_unit_dice_has_0_probability = [
            ten_unit_dice_probability[i] - ten_unit_dice_no_0_probability[i] for i in range(10)]

        success_rate = 0.9*sum(ten_unit_dice_has_0_probability[:ten_unit]) + \
            1*sum(ten_unit_dice_no_0_probability[:ten_unit]) + \
            (one_unit/10)*ten_unit_dice_has_0_probability[ten_unit] + \
            (one_unit/10+0.1)*ten_unit_dice_no_0_probability[ten_unit]

        result_100_rate = sum(ten_unit_dice_has_0_probability) * 0.1
        result_gt_95_rate = ten_unit_dice_probability[9] * 0.4

        return [success_rate, result_gt_95_rate, result_100_rate]
    if status == "b":
        ten_unit = original//10
        one_unit = original % 10
        ten_unit_dice_count = 1+count
        ten_unit_dice_probability_ = [
            ((10-n)/10)**ten_unit_dice_count for n in range(10)]
        ten_unit_dice_probability = [0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0.1**ten_unit_dice_count]
        for i in range(9):
            ten_unit_dice_probability[i] = ten_unit_dice_probability_[
                i]-ten_unit_dice_probability_[i+1]
        del ten_unit_dice_probability_

        ten_unit_0_is_pure_probability = 0.1**ten_unit_dice_count
        ten_unit_0_second_smallest_number_probability = [0]
        A_n_n = math.factorial(ten_unit_dice_count)
        for k in range(1, 9):
            val = sum([((9-k)**(ten_unit_dice_count-i))*(i-1)
                      for i in range(2, ten_unit_dice_count+1)])
            val = val*A_n_n
            val = val/(10**ten_unit_dice_count)
            ten_unit_0_second_smallest_number_probability.append(val)
        ten_unit_0_second_smallest_number_probability.append(
            ((ten_unit_dice_count-1)*A_n_n)/(10**ten_unit_dice_count))

        if ten_unit == 0:
            success_rate = ten_unit_dice_probability[0]*(one_unit/10)
        else:
            success_rate = sum(ten_unit_dice_probability[1:ten_unit]) * 1 + \
                ten_unit_dice_probability[ten_unit] * (one_unit/10 + 0.1) + \
                sum(ten_unit_0_second_smallest_number_probability[1:ten_unit]) * 1 + \
                ten_unit_0_second_smallest_number_probability[ten_unit] * (one_unit/10 + 0.1) + \
                ten_unit_0_is_pure_probability * 0.9

        result_100_rate = ten_unit_0_is_pure_probability*0.1
        result_gt_95_rate = ten_unit_dice_probability[9] * 0.4
        return [success_rate, result_gt_95_rate, result_100_rate]


if args.bonus:
    result = calculate(args.original, "b", args.count)
    print(
        f"The result of bonus dices: \noverall success rate: {result[0]:.4f}%;\n96~99 rate: {result[1]:.4f}%;\n100 rate: {result[2]:.4f}%")
if args.penlty:
    result = calculate(args.original, "p", args.count)
    print(
        f"The result of penlty dices: \noverall success rate: {result[0]:.4f}%;\n96~99 rate: {result[1]:.4f}%;\n100 rate: {result[2]:.4f}%")
