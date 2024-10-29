from supervisor import Supervisor

if __name__=='__main__':
    supervisor = Supervisor()
    while True:
        user_task = input("Enter a task or 'exit' to quit: ")
        if user_task.lower() == 'exit':
            print("Exiting assistant.")
            break
        supervisor.process_task(user_task)