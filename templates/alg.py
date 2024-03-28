def calculate_sale_price(avg_price, avg_initial_kms, current_kms):
    depreciation_rate = 0.1  # You can adjust this value based on your assumptions
    kms_driven = current_kms - avg_initial_kms
    depreciated_price = avg_price * (1 - depreciation_rate) ** (kms_driven / 10000)
    return depreciated_price

def main():
    num_cars = int(input("Enter the number of cars: "))
    car_data = []
    total_price = 0
    total_initial_kms = 0

    for i in range(num_cars):
        print(f"\nEnter details for car {i+1}:")
        current_price = float(input("Enter the current sale price of the car: "))
        initial_kms = int(input("Enter the initial kilometers driven: "))
        car_data.append((current_price, initial_kms))
        total_price += current_price
        total_initial_kms += initial_kms

    avg_price = total_price / num_cars
    avg_initial_kms = total_initial_kms / num_cars

    target_kms = int(input("\nEnter the target kilometers for estimating sale price: "))

    estimated_sale_price = calculate_sale_price(avg_price, avg_initial_kms, target_kms)
    print(f"\nEstimated sale price for a car with {target_kms} kilometers: ${estimated_sale_price:.2f}")

if __name__ == "__main__":
    main()
