import os
import json
from collections import Counter
from datetime import datetime, timedelta
import time

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.default_file = "tasks.json"
        self.projects = {}

        # Carica automaticamente i task dal file predefinito se esiste
        try:
            if os.path.exists(self.default_file):
                with open(self.default_file, "r") as file:
                    self.tasks = json.load(file)
                print(f"Tasks loaded automatically from {self.default_file}")
        except Exception as e:
            print(f"Error loading tasks from default file: {e}")

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_tasks(self):
        self.clear_screen()
        if not self.tasks:
            print("No tasks added yet.")
        else:
            print("Tasks:")
            for idx, task in enumerate(self.tasks, start=1):
                status = "Completed" if task["completed"] else "Pending"
                priority = f"[{task.get('priority', '-')}]" if 'priority' in task else ""
                due_date = f"Due: {task.get('due_date', 'No date')}" if 'due_date' in task else ""
                print(f"{idx}. {task['task']} {priority} - {status} {due_date}")

                
    def show_task_details(self):
        self.clear_screen()
        self.display_tasks()
        if not self.tasks:
            print("No tasks to show details.")
            return

        try:
            task_index = int(input("Enter the task number to view details: ")) - 1
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                print("\nTask Details:")
                print(f"Task: {task['task']}")
                print(f"Priority: {task.get('priority', 'Not set')}")
                print(f"Completed: {'Yes' if task['completed'] else 'No'}")
                
                # Mostro le nuove informazioni se presenti
                if 'due_date' in task:
                    print(f"Due Date: {task['due_date']}")
                if 'estimated_time' in task:
                    print(f"Estimated Time: {task['estimated_time']} minutes")
                if 'recurrence' in task:
                    print(f"Recurrence: {task['recurrence']}")
                if 'reminder' in task:
                    print(f"Reminder: {task['reminder']}")
                if 'tags' in task:
                    print(f"Tags: {', '.join(task['tags'])}")
                
                # Mostra sottotask
                if 'subtasks' in task:
                    print("\nSubtasks:")
                    for i, subtask in enumerate(task['subtasks'], 1):
                        status = "Completed" if subtask["completed"] else "Pending"
                        print(f"  {i}. {subtask['task']} - {status}")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

            
    def _save_tasks_to_default(self):
        """Salva i task nel file predefinito senza chiedere conferma"""
        try:
            with open(self.default_file, "w") as file:
                json.dump(self.tasks, file)
            return True
        except Exception as e:
            print(f"Error saving tasks to default file: {e}")
            return False
        
    def add_task(self):
        self.clear_screen()
        task = input("Enter the task: ")
        new_task = {"task": task, "completed": False}
        
        # Ask for priority right away
        priority_choice = input("Set priority (L=Low, M=Medium, H=High, Enter=None): ").upper()
        if priority_choice == "L":
            new_task["priority"] = "Low"
        elif priority_choice == "M":
            new_task["priority"] = "Medium"
        elif priority_choice == "H":
            new_task["priority"] = "High"
        
        # Ask if user wants to add a due date
        due_date_choice = input("Add due date? (y/n): ").lower()
        if due_date_choice == "y":
            due_date = input("Enter due date (YYYY-MM-DD): ")
            try:
                due_datetime = datetime.strptime(due_date, "%Y-%m-%d")
                new_task["due_date"] = due_datetime.strftime("%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Due date not set.")
        
        self.tasks.append(new_task)
        print("Task added successfully!")


    def mark_completed(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to mark as completed.")
            return

        try:
            task_index = int(input("Enter the task number to mark as completed: ")) - 1
            if 0 <= task_index < len(self.tasks):
                self.tasks[task_index]["completed"] = True
                print("Task marked as completed!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    def remove_task(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to remove.")
            return

        try:
            task_index = int(input("Enter the task number to remove: ")) - 1
            if 0 <= task_index < len(self.tasks):
                del self.tasks[task_index]
                print("Task removed successfully!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    def save_tasks_to_file(self):
        if not self.tasks:
            return

        default_choice = input(f"Do you want to save tasks to the default file '{self.default_file}'? (yes/no): ").lower()
        if default_choice == "yes":
            file_name = self.default_file
        else:
            file_name = input("Enter file name to save tasks (e.g., tasks.json): ")
        try:
            with open(file_name, "w") as file:
                json.dump(self.tasks, file)
            print("Tasks saved to file successfully!")
        except Exception as e:
            print(f"Error saving tasks to file: {e}")
    
    def load_tasks_from_file(self):
        file_name = input("Enter file name to load tasks from (e.g., tasks.json): ")
        try:
            with open(file_name, "r") as file:
                self.tasks = json.load(file)
            print("Tasks loaded from file successfully!")
        except FileNotFoundError:
            print("File not found.")
        except json.decoder.JSONDecodeError:
            print("Invalid JSON format in the file.")
        except Exception as e:
            print(f"Error loading tasks from file: {e}")

    def search_task(self):
        self.clear_screen()
        if not self.tasks:
            print("No tasks to search.")
            return

        search_term = input("Enter the task to search: ").lower()
        found_tasks = [task for task in self.tasks if search_term in task['task'].lower()]
        if found_tasks:
            print("Matching Tasks:")
            for idx, task in enumerate(found_tasks, start=1):
                status = "Completed" if task["completed"] else "Pending"
                print(f"{idx}. {task['task']} - {status}")
        else:
            print("No matching tasks found.")

    def sort_tasks(self):
        self.clear_screen()
        if not self.tasks:
            print("No tasks to sort.")
            return

        sorted_tasks = sorted(self.tasks, key=lambda x: x['task'].lower())
        self.tasks = sorted_tasks
        print("Tasks sorted successfully!")

    def display_statistics(self):
        self.clear_screen()
        if not self.tasks:
            print("No tasks added yet.")
            return

        task_statuses = [task['completed'] for task in self.tasks]
        task_counter = Counter(task_statuses)
        completed_tasks = task_counter[True]
        pending_tasks = task_counter[False]
        print(f"Completed Tasks: {completed_tasks}")
        print(f"Pending Tasks: {pending_tasks}")

    def clear_all_tasks(self):
        self.clear_screen()
        if not self.tasks:
            print("No tasks to clear.")
            return

        confirm_clear = input("Are you sure you want to clear all tasks? (yes/no): ").lower()
        if confirm_clear == "yes" or confirm_clear == "y" :
            self.tasks = []
            print("All tasks cleared successfully!")
        else:
            print("Operation cancelled.")

    def edit_task(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to edit.")
            return

        try:
            task_index = int(input("Enter the task number to edit: ")) - 1
            if 0 <= task_index < len(self.tasks):
                new_task = input("Enter the new task: ")
                self.tasks[task_index]["task"] = new_task
                print("Task edited successfully!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    def view_completed_tasks(self):
        completed_tasks = [task for task in self.tasks if task["completed"]]
        if not completed_tasks:
            print("No completed tasks.")
        else:
            print("Completed Tasks:")
            for idx, task in enumerate(completed_tasks, start=1):
                print(f"{idx}. {task['task']}")

    def view_pending_tasks(self):
        pending_tasks = [task for task in self.tasks if not task["completed"]]
        if not pending_tasks:
            print("No pending tasks.")
        else:
            print("Pending Tasks:")
            for idx, task in enumerate(pending_tasks, start=1):
                print(f"{idx}. {task['task']}")

    def count_tasks(self):
        total_tasks = len(self.tasks)
        print(f"Total number of tasks: {total_tasks}")

    def undo_marked_task(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to undo.")
            return

        try:
            task_index = int(input("Enter the task number to mark as pending again: ")) - 1
            if 0 <= task_index < len(self.tasks):
                self.tasks[task_index]["completed"] = False
                print("Task marked as pending again!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")
    
    def set_priority(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to set priority.")
            return

        try:
            task_index = int(input("Enter the task number to set priority: ")) - 1
            if 0 <= task_index < len(self.tasks):
                priority = input("Enter priority level (Low/Medium/High): ").capitalize()
                if priority in ["Low", "Medium", "High"]:
                    self.tasks[task_index]["priority"] = priority
                    print("Priority set successfully!")
                else:
                    print("Invalid priority level. Please enter Low, Medium, or High.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    def show_task_details(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to show details.")
            return

        try:
            task_index = int(input("Enter the task number to view details: ")) - 1
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                print("Task Details:")
                print(f"Task: {task['task']}")
                print(f"Priority: {task.get('priority', 'Not set')}")
                print(f"Completed: {'Yes' if task['completed'] else 'No'}")
                # Add more details as needed (e.g., due date, tags, etc.)
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    def archive_tasks(self):
        completed_tasks = [task for task in self.tasks if task["completed"]]
        if not completed_tasks:
            print("No completed tasks to archive.")
            return

        archive_name = "archive.json"  
        try:
            with open(archive_name, "a") as file:
                for task in completed_tasks:
                    json.dump(task, file)
                    file.write("\n")
            print("Completed tasks archived successfully!")
        except Exception as e:
            print(f"Error archiving tasks: {e}")
    
    def set_reminder(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to set reminders.")
            return

        try:
            task_index = int(input("Enter the task number to set a reminder: ")) - 1
            if 0 <= task_index < len(self.tasks):
                reminder_date = input("Enter the reminder date (YYYY-MM-DD): ")
                try:
                    reminder_datetime = datetime.strptime(reminder_date, "%Y-%m-%d")
                    self.tasks[task_index]["reminder"] = reminder_datetime.strftime("%Y-%m-%d")
                    print("Reminder set successfully!")
                except ValueError:
                    print("Invalid date format. Please enter in YYYY-MM-DD format.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    def set_task_tags(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to add tags/categories.")
            return

        try:
            task_index = int(input("Enter the task number to add tags/categories: ")) - 1
            if 0 <= task_index < len(self.tasks):
                tags = input("Enter tags/categories separated by commas: ")
                tag_list = [tag.strip() for tag in tags.split(",")]
                self.tasks[task_index]["tags"] = tag_list
                print("Tags/categories added successfully!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")

    # --- NUOVE FUNZIONI PER LA GESTIONE DEI PROGETTI ---
    
    def create_project(self):
        self.clear_screen()
        project_name = input("Enter project name: ")
        if project_name in self.projects:
            print(f"Project '{project_name}' already exists.")
            return
            
        self.projects[project_name] = []
        print(f"Project '{project_name}' created successfully!")
    
    def display_projects(self):
        self.clear_screen()
        if not self.projects:
            print("No projects created yet.")
            return
        
        print("Projects:")
        for idx, (name, tasks) in enumerate(self.projects.items(), 1):
            task_count = len(tasks)
            completed = sum(1 for t in tasks if t["completed"])
            print(f"{idx}. {name} - {completed}/{task_count} completed")
    
    def add_task_to_project(self):
        self.clear_screen()
        if not self.projects:
            print("No projects created yet. Create a project first.")
            return
            
        print("Available Projects:")
        project_names = list(self.projects.keys())
        for idx, name in enumerate(project_names, 1):
            print(f"{idx}. {name}")
        
        try:
            project_idx = int(input("Select project number: ")) - 1
            if 0 <= project_idx < len(project_names):
                project_name = project_names[project_idx]
                task = input("Enter the task: ")
                self.projects[project_name].append({"task": task, "completed": False})
                print(f"Task added to project '{project_name}' successfully!")
            else:
                print("Invalid project number.")
        except ValueError:
            print("Please enter a valid project number.")
    
    # --- NUOVE FUNZIONI PER I SOTTOTASK ---
    
    def add_subtask(self):
        self.display_tasks()
        if not self.tasks:
            print("No parent tasks available to add subtasks.")
            return

        try:
            task_index = int(input("Enter parent task number: ")) - 1
            if 0 <= task_index < len(self.tasks):
                subtask = input("Enter subtask description: ")
                if not "subtasks" in self.tasks[task_index]:
                    self.tasks[task_index]["subtasks"] = []
                self.tasks[task_index]["subtasks"].append({"task": subtask, "completed": False})
                print("Subtask added successfully!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")
    
    def complete_subtask(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks available.")
            return

        try:
            task_index = int(input("Enter parent task number: ")) - 1
            if 0 <= task_index < len(self.tasks) and "subtasks" in self.tasks[task_index]:
                subtasks = self.tasks[task_index]["subtasks"]
                print("\nSubtasks:")
                for i, subtask in enumerate(subtasks, 1):
                    status = "Completed" if subtask["completed"] else "Pending"
                    print(f"  {i}. {subtask['task']} - {status}")
                
                subtask_index = int(input("\nEnter subtask number to mark as completed: ")) - 1
                if 0 <= subtask_index < len(subtasks):
                    subtasks[subtask_index]["completed"] = True
                    print("Subtask marked as completed!")
                else:
                    print("Invalid subtask number.")
            else:
                print("Invalid task number or no subtasks available.")
        except ValueError:
            print("Please enter a valid number.")
    
    # --- NUOVE FUNZIONI PER LA GESTIONE TEMPORALE ---
    
    def set_due_date(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to set due date.")
            return

        try:
            task_index = int(input("Enter the task number to set due date: ")) - 1
            if 0 <= task_index < len(self.tasks):
                due_date = input("Enter due date (YYYY-MM-DD): ")
                try:
                    due_datetime = datetime.strptime(due_date, "%Y-%m-%d")
                    self.tasks[task_index]["due_date"] = due_datetime.strftime("%Y-%m-%d")
                    print("Due date set successfully!")
                except ValueError:
                    print("Invalid date format. Please enter in YYYY-MM-DD format.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")
    
    def set_recurrence(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to set recurrence.")
            return

        try:
            task_index = int(input("Enter the task number to set recurrence: ")) - 1
            if 0 <= task_index < len(self.tasks):
                print("\nRecurrence options:")
                print("1. Daily")
                print("2. Weekly")
                print("3. Monthly")
                print("4. Custom (specify days)")
                
                choice = input("Choose recurrence pattern (1-4): ")
                recurrence = None
                
                if choice == "1":
                    recurrence = "daily"
                elif choice == "2":
                    recurrence = "weekly"
                elif choice == "3":
                    recurrence = "monthly"
                elif choice == "4":
                    days = input("Enter number of days between recurrences: ")
                    if days.isdigit():
                        recurrence = f"every {days} days"
                    else:
                        print("Invalid input. Please enter a number.")
                        return
                else:
                    print("Invalid choice.")
                    return
                    
                self.tasks[task_index]["recurrence"] = recurrence
                print(f"Recurrence set to '{recurrence}' successfully!")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")
    
    # --- NUOVE FUNZIONI PER LA VISUALIZZAZIONE ---
    
    def show_dashboard(self):
        self.clear_screen()
        print("=== TASK DASHBOARD ===")
        
        if not self.tasks:
            print("No tasks available.")
            return
            
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task["completed"])
        completion_percentage = int((completed / total * 100) if total > 0 else 0)
        
        print(f"Progress: {completed}/{total} ({completion_percentage}% complete)")
        
        # Tasks due today
        today = datetime.now().strftime("%Y-%m-%d")
        due_today = [t for t in self.tasks if t.get("due_date") == today and not t["completed"]]
        
        # Tasks due soon (within next 3 days)
        future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        due_soon = [t for t in self.tasks if t.get("due_date") and 
                   today < t.get("due_date") <= future_date and not t["completed"]]
        
        # High priority tasks
        high_priority = [t for t in self.tasks if t.get("priority") == "High" and not t["completed"]]
        
        print(f"\nTasks due today: {len(due_today)}")
        print(f"Tasks due within 3 days: {len(due_soon)}")
        print(f"High priority tasks: {len(high_priority)}")
        
        # Display top tasks
        if due_today:
            print("\nDUE TODAY:")
            for i, task in enumerate(due_today[:3], 1):  # Show top 3
                print(f"- {task['task']}")
        
        if high_priority:
            print("\nHIGH PRIORITY TASKS:")
            for i, task in enumerate(high_priority[:3], 1):  # Show top 3
                print(f"- {task['task']}")
        
        input("\nPress Enter to continue...")
    
    def kanban_view(self):
        self.clear_screen()
        if not self.tasks:
            print("No tasks available for Kanban view.")
            return
            
        todo = [t for t in self.tasks if not t["completed"]]
        done = [t for t in self.tasks if t["completed"]]
        
        print("=== KANBAN VIEW ===")
        print("\nTO DO:")
        if todo:
            for i, t in enumerate(todo[:10], 1):  # Show top 10
                priority = f"[{t.get('priority', '-')}]" if 'priority' in t else ""
                print(f"{i}. {t['task']} {priority}")
        else:
            print("No pending tasks.")
            
        print("\nCOMPLETED:")
        if done:
            for i, t in enumerate(done[:5], 1):  # Show top 5
                print(f"{i}. {t['task']}")
        else:
            print("No completed tasks.")
            
        input("\nPress Enter to continue...")
    
    # --- NUOVE FUNZIONI PER L'ANALISI DI PRODUTTIVITÀ ---
    
    def productivity_analysis(self):
        self.clear_screen()
        print("=== PRODUCTIVITY ANALYSIS ===")
        
        if not self.tasks:
            print("No tasks available for analysis.")
            return
        
        # Tasks by priority
        priorities = Counter([t.get("priority", "None") for t in self.tasks])
        print("\nTasks by priority:")
        for priority, count in priorities.items():
            print(f"- {priority}: {count}")
        
        # Tasks by tag
        all_tags = []
        for task in self.tasks:
            if "tags" in task:
                all_tags.extend(task["tags"])
        
        if all_tags:
            tag_counts = Counter(all_tags)
            print("\nTasks by tag:")
            for tag, count in tag_counts.most_common(5):  # Top 5 tags
                print(f"- {tag}: {count}")
        
        # Completion rate
        completion_rate = sum(1 for t in self.tasks if t["completed"]) / len(self.tasks) * 100
        print(f"\nOverall completion rate: {completion_rate:.1f}%")
        
        # Due date analysis
        overdue = 0
        today = datetime.now().strftime("%Y-%m-%d")
        for task in self.tasks:
            if not task["completed"] and task.get("due_date") and task.get("due_date") < today:
                overdue += 1
        
        if overdue > 0:
            print(f"\nOverdue tasks: {overdue}")
            
        input("\nPress Enter to continue...")
    
    def estimate_task_time(self):
        self.display_tasks()
        if not self.tasks:
            print("No tasks to estimate time.")
            return

        try:
            task_index = int(input("Enter the task number to estimate time: ")) - 1
            if 0 <= task_index < len(self.tasks):
                estimated_minutes = input("Enter estimated time (in minutes): ")
                try:
                    self.tasks[task_index]["estimated_time"] = int(estimated_minutes)
                    print("Time estimate added successfully!")
                except ValueError:
                    print("Please enter a valid number.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Please enter a valid task number.")
    
    # --- NUOVE FUNZIONI PER BACKUP E AUTOMAZIONE ---
    
    def auto_backup(self):
        if not self.tasks:
            print("No tasks to backup.")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}.json"
        
        try:
            with open(backup_file, "w") as file:
                json.dump(self.tasks, file)
            print(f"Auto-backup created: {backup_file}")
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    # --- NUOVE FUNZIONI PER L'INTERFACCIA UTENTE ---
    
    def focus_mode(self):
        self.clear_screen()
        print("=== FOCUS MODE ===")
        
        high_priority = [t for t in self.tasks if t.get("priority") == "High" and not t["completed"]]
        due_today = [t for t in self.tasks if t.get("due_date") == datetime.now().strftime("%Y-%m-%d") and not t["completed"]]
        
        focus_tasks = high_priority + [t for t in due_today if t not in high_priority]
        
        if not focus_tasks:
            print("No high priority or due tasks found for focus mode.")
            return
            
        print("Focus on these important tasks:")
        for i, task in enumerate(focus_tasks, 1):
            priority = f"[{task.get('priority', '-')}]" if 'priority' in task else ""
            due_date = f"Due: {task.get('due_date', 'No date')}" if 'due_date' in task else ""
            print(f"{i}. {task['task']} {priority} {due_date}")
        
        try:
            choice = input("\nSelect a task to focus on (or Enter to exit): ")
            if choice and choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(focus_tasks):
                    chosen_task = focus_tasks[choice-1]
                    
                    self.clear_screen()
                    print(f"FOCUSING ON: {chosen_task['task']}")
                    if "estimated_time" in chosen_task:
                        print(f"Estimated time: {chosen_task['estimated_time']} minutes")
                    
                    print("\n[Press Enter when completed or Ctrl+C to exit]")
                    
                    try:
                        # Timer functionality
                        start_time = time.time()
                        input()
                        elapsed_time = int(time.time() - start_time)
                        minutes = elapsed_time // 60
                        seconds = elapsed_time % 60
                        print(f"Task worked on for {minutes} minutes and {seconds} seconds")
                        
                        mark_complete = input("Mark this task as completed? (y/n): ").lower()
                        if mark_complete == 'y':
                            # Find the task in the main tasks list and mark it completed
                            for task in self.tasks:
                                if task == chosen_task:
                                    task["completed"] = True
                                    print("Task marked as completed!")
                                    break
                    except KeyboardInterrupt:
                        print("\nFocus mode exited.")
                else:
                    print("Invalid task number.")
        except ValueError:
            print("Please enter a valid number.")
    
    def check_reminders(self):
        today = datetime.now().strftime("%Y-%m-%d")
        due_tasks = [t for t in self.tasks if t.get("reminder") == today and not t["completed"]]
        
        if due_tasks:
            self.clear_screen()
            print("\n🔔 REMINDERS TODAY:")
            for task in due_tasks:
                print(f"- {task['task']}")
            print("\n")

    
    def show_menu(self):
        print("\nTask Manager")
        print("1. Add Task: Adds a new task to the list.")
        print("2. List Tasks: Displays the list of tasks.")
        print("3. Mark Task as Completed: Marks a task as completed.")
        print("4. Remove Task: Removes a task from the list.")
        print("5. Save Tasks to File: Saves tasks to a file.")
        print("6. Load Tasks from File: Loads tasks from a file.")
        print("7. Search Task: Searches for tasks containing a specific term.")
        print("8. Sort Tasks: Sorts tasks alphabetically.")
        print("9. Display Statistics: Displays statistics for completed and pending tasks.")
        print("10. Clear All Tasks: Clears all tasks.")
        print("11. Edit Task: Edits an existing task.")
        print("12. View Completed Tasks: Displays completed tasks.")
        print("13. View Pending Tasks: Displays pending tasks.")
        print("14. Count Tasks: Displays the total number of tasks.")
        print("15. Undo Marked Task: Reverts a completed task to pending.")
        print("16. Set Priority: Sets priority for a task.")
        print("17. Show Task Details: Displays detailed information about a task.")
        print("18. Set Reminder: Sets a reminder for a task.")
        print("19. Set Task Tags: Adds tags/categories to a task.")
        print("20. Archive Completed Tasks: Archives completed tasks.")
        print("21. Exit: Exits the Task Manager.")

    def start(self):
        while True:
            self.show_menu()
            choice = input("Enter your choice: ")

            match choice:
                case "1":
                    self.add_task()
                case "2":
                    self.display_tasks()
                case "3":
                    self.mark_completed()
                case "4":
                    self.remove_task()
                case "5":
                    self.save_tasks_to_file()
                case "6":
                    self.load_tasks_from_file()
                case "7":
                    self.search_task()
                case "8":
                    self.sort_tasks()
                case "9":
                    self.display_statistics()
                case "10":
                    self.clear_all_tasks()
                case "11":
                    self.edit_task()
                case "12":
                    self.view_completed_tasks()
                case "13":
                    self.view_pending_tasks()
                case "14":
                    self.count_tasks()
                case "15":
                    self.undo_marked_task()
                case "16":
                    self.set_priority()
                case "17":
                    self.show_task_details()
                case "18":
                    self.set_reminder()
                case "19":
                    self.set_task_tags()
                case "20":
                    self.archive_tasks()
                # Nuove opzioni di menu:
                case "21":
                    self.create_project()
                case "22":
                    self.display_projects()
                case "23":
                    self.add_task_to_project()
                case "24":
                    self.add_subtask()
                case "25":
                    self.complete_subtask()
                case "26":
                    self.set_due_date()
                case "27":
                    self.set_recurrence()
                case "28":
                    self.show_dashboard()
                case "29":
                    self.kanban_view()
                case "30":
                    self.productivity_analysis()
                case "31":
                    self.estimate_task_time()
                case "32":
                    self.auto_backup()
                case "33":
                    self.focus_mode()
                case "0":
                    print("Exiting Task Manager. Goodbye!")
                    break
                case _:
                    self.clear_screen()
                    print("Invalid choice. Please choose a valid option.")

if __name__ == "__main__":
    task_manager = TaskManager()
    task_manager.start()
