def parse_csv_lines(lines):
    clients = []
    for row_client in lines:
        parts = row_client.split(sep=", ", maxsplit=2)
        if len(parts) != 3:
            city, age, name = None, None, None
        else:
            city, age, name = parts
            try:
                age = int(age)
            except ValueError:
                age = None
        clients.append({"city": city, "age": age, "name": name})
    return clients

    clients.append({"city": city.split(), "age": age.split(), "name": name.split()})


def main():
    row_clients = ["Moscov, 21, Ivan", "Minsk, 18, Rostislav", "Mogilev, 16, Ira"]
    clients = parse_csv_lines(row_clients)
    print(clients)


if __name__ == "__main__":
    main()
