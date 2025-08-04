import os
import time
import datetime
from src.utils import random_test_case, generate_goods, apply_perturbation
from src.player import Player
from tests.test_runner import run_tests
from src.failed_test_storage import FailedTestStorage
from src.phase2_test_storage import Phase2TestStorage
from src.config import config

def clear_terminal():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def write_log(log_file, message):
    """Write a log message to the log file with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

# Initialize failed test storage
failed_test_storage = FailedTestStorage()

# Initialize Phase 2 test storage
phase2_test_storage = Phase2TestStorage()

def single_test_mode():
    """Run a single test with user-specified number of goods."""
    clear_terminal()
    print("=" * 60)
    print("SINGLE TEST MODE")
    print("=" * 60)
    
    while True:
        try:
            k = int(input("\nEnter number of goods (K): "))
            if k <= 0:
                print("Please enter a number greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
    
    print(f"\nRunning test with {k} goods...")
    
    start_time = time.time()
    goods, players, epsilon = random_test_case(k)
    print(f"Using perturbation with epsilon = {epsilon:.10f}")
    
    results = run_tests(goods, players)
    end_time = time.time()
    
    execution_time = end_time - start_time
    is_efx = results['algorithm']['is_efx']
    
    print(f"\nExecution time: {execution_time:.3f} seconds")
    print(f"Result: {'EFX' if is_efx else 'Not EFX'}")
    
    # If we find Non-EFX, show detailed information and save the failed test
    if not is_efx:
        print("\n" + "=" * 60)
        print("NON-EFX CASE ANALYSIS")
        print("=" * 60)
        print(f"Number of goods (K): {k}")
        print(f"Perturbation epsilon: {epsilon:.10f}")
        print(f"Goods: {goods}")

        # Show player valuations
        print(f"\nPLAYER VALUATIONS:")
        print("-" * 50)
        for player in players:
            print(f"{player.name}: {player.valuation}")
        print("=" * 60)
        
        # Save failed test case
        failed_test_storage.save_failed_test(goods, players, "single")
    
    # Save Phase 2 test case if Phase 2 was executed
    phase2_info = results['algorithm']['phase2_info']
    if phase2_info['executed']:
        phase2_test_storage.save_phase2_test(goods, players, "single", phase2_info)
    
    # Log the result
    log_message = f"SINGLE_TEST: K={k}, EFX={is_efx}, Time={execution_time:.3f}s"
    
    # Add Phase 2 information to log
    phase2_info = results['algorithm']['phase2_info']
    if phase2_info['executed']:
        log_message += f", Phase2=YES, Steps={phase2_info['steps']}"
        log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
        log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
        if phase2_info['efx_achieved_in_phase2']:
            log_message += ", EFX_ViaPhase2=YES"
    else:
        log_message += ", Phase2=NO"
    
    if not is_efx:
        log_message += f", Goods={goods}, Epsilon={epsilon:.10f}"
    write_log("efx_test_logs.txt", log_message)
    
    input("\nPress Enter to continue...")

def continuous_test_mode():
    """Run continuous tests until a non-EFX result is found."""
    clear_terminal()
    print("=" * 60)
    print("CONTINUOUS TEST MODE")
    print("=" * 60)
    
    while True:
        try:
            k = int(input("\nEnter number of goods (K): "))
            if k <= 0:
                print("Please enter a number greater than 0")
                continue
            break
        except ValueError:
            print("Please enter a valid number")
    
    print(f"\nStarting continuous tests with {k} goods...")
    print("Searching until finding a Non-EFX result...")
    input("Press Enter to begin...")
    
    start_time = time.time()
    efx_count = 0
    test_count = 0
    total_test_time = 0
    phase2_count = 0  # Counter for tests that enter Phase 2
    
    try:
        while True:
            test_count += 1
            clear_terminal()
            
            current_time = time.time()
            elapsed_time = current_time - start_time
        
            print("=" * 60)
            print("CONTINUOUS TEST IN PROGRESS")
            print("=" * 60)
            print(f"Test #{test_count}")
            print(f"EFX found: {efx_count}")
            print(f"Elapsed time: {elapsed_time:.1f} seconds")
            if efx_count > 0:
                avg_time = total_test_time / efx_count
                print(f"Average time per EFX: {avg_time:.3f} seconds")
            if test_count > 1:  # Only show Phase 2 stats after first test
                phase2_percentage = (phase2_count / (test_count - 1)) * 100
                print(f"Phase 2 usage: {phase2_count}/{test_count - 1} tests ({phase2_percentage:.1f}%)")
            print("=" * 60)
            
            test_start = time.time()
            goods, players, epsilon = random_test_case(k)
            results = run_tests(goods, players)
            test_end = time.time()
            
            test_duration = test_end - test_start
            total_test_time += test_duration
            is_efx = results['algorithm']['is_efx']
            
            # Check if this test entered Phase 2
            phase2_info = results['algorithm']['phase2_info']
            if phase2_info['executed']:
                phase2_count += 1
                # Save Phase 2 test case
                phase2_test_storage.save_phase2_test(goods, players, "continuous", phase2_info)
            
            if is_efx:
                efx_count += 1
                # Log EFX result with Phase 2 information
                log_message = f"CONTINUOUS_TEST: Test#{test_count}, K={k}, EFX=True, TestTime={test_duration:.3f}s, TotalTime={elapsed_time:.1f}s"
                
                # Add Phase 2 information
                if phase2_info['executed']:
                    log_message += f", Phase2=YES, Steps={phase2_info['steps']}"
                    log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
                    log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
                    if phase2_info['efx_achieved_in_phase2']:
                        log_message += ", EFX_ViaPhase2=YES"
                else:
                    log_message += ", Phase2=NO"
                
                write_log("efx_test_logs.txt", log_message)
            else:
                # Found non-EFX result!
                # NO CLEAR TERMINAL
                final_time = time.time() - start_time
                avg_time = total_test_time / efx_count if efx_count > 0 else 0
                
                print("\n" + "=" * 60)
                print("NON-EFX RESULT FOUND!")
                print("=" * 60)
                print(f"Total tests performed: {test_count}")
                print(f"EFX results found: {efx_count}")
                print(f"Non-EFX result in test #{test_count}")
                print(f"Total execution time: {final_time:.1f} seconds")
                if efx_count > 0:
                    print(f"Average time per EFX: {avg_time:.3f} seconds")
                else:
                    print("No EFX results found before Non-EFX")
                
                # Show Phase 2 statistics
                phase2_percentage = (phase2_count / test_count) * 100 if test_count > 0 else 0
                print(f"\nPHASE 2 STATISTICS:")
                print(f"Tests that entered Phase 2: {phase2_count}/{test_count} ({phase2_percentage:.1f}%)")
                
                # Show detailed information of the problematic case
                print("\n" + "=" * 80)
                print("NON-EFX CASE INFORMATION")
                print("=" * 80)
                print(f"Number of goods (K): {k}")
                print(f"Perturbation epsilon: {epsilon:.10f}")
                print(f"Goods: {goods}")
                
                # Show player valuations
                print(f"\nPLAYER VALUATIONS:")
                print("-" * 50)
                for player in players:
                    print(f"{player.name}: {player.valuation}")
                
                print("=" * 60)
                
                # Save failed test case
                failed_test_storage.save_failed_test(goods, players, "continuous")
                
                # Log final result with Phase 2 information
                log_message = f"NON_EFX_FOUND: Test#{test_count}, K={k}, EFX_Count={efx_count}, TotalTime={final_time:.1f}s, AvgTimePerEFX={avg_time:.3f}s"
                
                # Add Phase 2 statistics
                phase2_percentage = (phase2_count / test_count) * 100 if test_count > 0 else 0
                log_message += f", Phase2_Tests={phase2_count}/{test_count}({phase2_percentage:.1f}%)"
                
                # Add Phase 2 information for this specific test
                phase2_info = results['algorithm']['phase2_info']
                if phase2_info['executed']:
                    log_message += f", LastTest_Phase2=YES, Steps={phase2_info['steps']}"
                    log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
                    log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
                else:
                    log_message += ", LastTest_Phase2=NO"
                
                log_message += f", Goods={goods}, Epsilon={epsilon:.10f}"
                write_log("efx_test_logs.txt", log_message)
                
                input("\nPress Enter to continue...")
                break
            
    except KeyboardInterrupt:
        # Handle manual interruption (Ctrl+C)
        final_time = time.time() - start_time
        avg_time = total_test_time / efx_count if efx_count > 0 else 0
        
        print("\n\n" + "=" * 60)
        print("TESTS INTERRUPTED BY USER")
        print("=" * 60)
        print(f"Total tests performed: {test_count}")
        print(f"EFX results found: {efx_count}")
        print(f"Total execution time: {final_time:.1f} seconds")
        if efx_count > 0:
            print(f"Average time per EFX: {avg_time:.3f} seconds")
        
        # Show Phase 2 statistics
        phase2_percentage = (phase2_count / test_count) * 100 if test_count > 0 else 0
        print(f"\nPHASE 2 STATISTICS:")
        print(f"Tests that entered Phase 2: {phase2_count}/{test_count} ({phase2_percentage:.1f}%)")
        
        # Log the interruption
        log_message = f"CONTINUOUS_INTERRUPTED: Tests={test_count}, EFX_Count={efx_count}, TotalTime={final_time:.1f}s"
        log_message += f", Phase2_Tests={phase2_count}/{test_count}({phase2_percentage:.1f}%)"
        write_log("efx_test_logs.txt", log_message)
        
        input("\nPress Enter to continue...")

def manual_test_mode():
    """Create and run a manual test case with custom goods and player valuations."""
    clear_terminal()
    print("=" * 60)
    print("MANUAL TEST MODE")
    print("=" * 60)
    print("Create a custom test case with specific goods and player valuations")
    print()
    
    try:
        # Get number of goods
        while True:
            try:
                k = int(input("Enter number of goods (2-12): ").strip())
                if 2 <= k <= 12:
                    break
                print("Please enter a number between 2 and 12")
            except ValueError:
                print("Please enter a valid number")
        
        # Generate goods names
        goods = generate_goods(k)
        print(f"\nGoods generated: {goods}")
        
        # Get player valuations
        players = []
        for i in range(4):
            player_name = f"P{i+1}"
            print(f"\n--- Player {player_name} Valuations ---")
            valuations = {}
            
            for good in goods:
                while True:
                    try:
                        value = float(input(f"Value for {good}: ").strip())
                        if value >= 0:
                            valuations[good] = value
                            break
                        print("Please enter a non-negative number")
                    except ValueError:
                        print("Please enter a valid number")
            
            players.append(Player(player_name, valuations))
        
        # Ask about perturbation
        print("\n" + "=" * 40)
        apply_perturb = input("Apply perturbation for non-degeneracy? (y/N): ").strip().lower()
        
        epsilon = None
        if apply_perturb in ['y', 'yes', 's', 'si', 'sí']:
            players, epsilon = apply_perturbation(players, goods)
            print(f"Applied perturbation with epsilon = {epsilon:.10f}")
        else:
            print("No perturbation applied")
        
        # Display test case summary
        print(f"\n" + "=" * 60)
        print("TEST CASE SUMMARY")
        print("=" * 60)
        print(f"Goods: {goods}")
        print(f"Perturbation epsilon: {epsilon if epsilon else 'None'}")
        print("\nPlayer valuations:")
        for player in players:
            print(f"{player.name}: {player.valuation}")
        
        print("\n" + "=" * 60)
        confirmation = input("Run this test case? (Y/n): ").strip().lower()
        if confirmation in ['', 'y', 'yes', 's', 'si', 'sí']:
            print("Running manual test case...")
            
            start_time = time.time()
            results = run_tests(goods, players)
            end_time = time.time()
            
            execution_time = end_time - start_time
            is_efx = results['algorithm']['is_efx']
            
            print(f"\nExecution time: {execution_time:.3f} seconds")
            print(f"Result: {'EFX' if is_efx else 'Not EFX'}")
            
            # Log the result with Phase 2 information
            log_message = f"MANUAL_TEST: K={k}, EFX={is_efx}, Time={execution_time:.3f}s, Epsilon={epsilon if epsilon else 'None'}"
            
            # Add Phase 2 information
            phase2_info = results['algorithm']['phase2_info']
            if phase2_info['executed']:
                log_message += f", Phase2=YES, Steps={phase2_info['steps']}"
                log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
                log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
                if phase2_info['efx_achieved_in_phase2']:
                    log_message += ", EFX_ViaPhase2=YES"
            else:
                log_message += ", Phase2=NO"
            
            write_log("efx_test_logs.txt", log_message)
            
            # Save Phase 2 test case if Phase 2 was executed
            if phase2_info['executed']:
                phase2_test_storage.save_phase2_test(goods, players, "manual", phase2_info)
            
            # If we find Non-EFX, save the failed test
            if not is_efx:
                print(f"\nNon-EFX result found!")
                save_failed = input("Save this as a failed test case? (Y/n): ").strip().lower()
                if save_failed in ['', 'y', 'yes', 's', 'si', 'sí']:
                    failed_test_storage.save_failed_test(goods, players, "manual")
                    print("Failed test case saved")
        else:
            print("Test cancelled")
    
    except KeyboardInterrupt:
        print("\nTest creation cancelled")
    except Exception as e:
        print(f"Error creating test case: {e}")
    
    input("\nPress Enter to continue...")

def show_menu():
    """Display the main menu."""
    clear_terminal()
    print("=" * 60)
    print("EFX ALLOCATION TESTING - 4 PLAYERS")
    print("=" * 60)
    print()
    print("AVAILABLE OPTIONS:")
    print()
    print("1. Run single test with K goods")
    print("2. Run continuous tests until finding Non-EFX")
    print("3. Create and run manual test case")
    print("4. View test logs")
    print("5. Clear logs")
    print("6. Failed tests management")
    print("7. Phase 2 management")
    print("8. Configuration settings")
    print("0. Exit")
    print()
    print("=" * 60)

def view_logs():
    """Display recent log entries."""
    clear_terminal()
    print("=" * 60)
    print("EFX TEST LOGS")
    print("=" * 60)
    
    try:
        with open("efx_test_logs.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("\nNo logs available.")
        else:
            # Show last 20 entries
            recent_lines = lines[-20:] if len(lines) > 20 else lines
            print(f"\nShowing the last {len(recent_lines)} entries:")
            print("-" * 60)
            for line in recent_lines:
                print(line.strip())
    except FileNotFoundError:
        print("\nLog file not found.")
    
    input("\nPress Enter to continue...")

def clear_logs():
    """Clear the log file."""
    clear_terminal()
    print("=" * 60)
    print("CLEAR LOGS")
    print("=" * 60)
    
    confirm = input("\nAre you sure you want to clear all logs? (y/N): ")
    if confirm.lower() in ['y', 'yes', 's', 'si', 'sí']:
        try:
            with open("efx_test_logs.txt", 'w', encoding='utf-8') as f:
                f.write("")
            print("Logs cleared successfully.")
        except Exception as e:
            print(f"Error clearing logs: {e}")
    else:
        print("Operation canceled.")
    
    input("\nPress Enter to continue...")

def failed_tests_management():
    """Manage failed test cases."""
    while True:
        clear_terminal()
        print("=" * 60)
        print("FAILED TESTS MANAGEMENT")
        print("=" * 60)
        
        count = failed_test_storage.get_failed_tests_count()
        print(f"Total failed test cases stored: {count}")
        print()
        print("AVAILABLE OPTIONS:")
        print()
        print("1. View all failed tests")
        print("2. Run old failed tests")
        print("3. Delete specific failed test")
        print("4. Delete multiple failed tests")
        print("5. Clear all failed tests")
        print("0. Back to main menu")
        print()
        print("=" * 60)
        
        try:
            choice = input("Select an option (0-5): ").strip()
            
            if choice == "1":
                view_failed_tests()
            elif choice == "2":
                run_old_failed_tests()
            elif choice == "3":
                delete_specific_failed_test()
            elif choice == "4":
                delete_multiple_failed_tests()
            elif choice == "5":
                clear_all_failed_tests()
            elif choice == "0":
                break
            else:
                print("Invalid option. Please select 0-5.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to continue...")

def view_failed_tests():
    """Display all stored failed test cases."""
    clear_terminal()
    print("=" * 60)
    print("FAILED TEST CASES")
    print("=" * 60)
    
    failed_test_storage.print_failed_tests_summary()
    input("\nPress Enter to continue...")

def run_old_failed_tests():
    """Run stored failed test cases."""
    clear_terminal()
    print("=" * 60)
    print("RUN OLD FAILED TESTS")
    print("=" * 60)
    
    count = failed_test_storage.get_failed_tests_count()
    if count == 0:
        print("No failed test cases stored.")
        input("\nPress Enter to continue...")
        return
    
    # Show summary of failed test cases
    failed_test_storage.print_failed_tests_summary()
    
    print("\nOptions:")
    print("1. Run a specific test case")
    print("2. Run all failed test cases")
    print("0. Back")
    print()
    
    choice = input("Select option (0-2): ").strip()
    
    if choice == "1":
        run_specific_failed_test()
    elif choice == "2":
        run_all_failed_tests()
    elif choice == "0":
        return
    else:
        print("Invalid option.")
        input("Press Enter to continue...")

def run_specific_failed_test():
    """Run a specific failed test case."""
    count = failed_test_storage.get_failed_tests_count()
    
    try:
        index = int(input(f"\nEnter test case number (1-{count}): "))
        test_case = failed_test_storage.get_failed_test_by_index(index)
        
        if test_case is None:
            print("Invalid test case number.")
            input("Press Enter to continue...")
            return
        
        print(f"\nRunning failed test case #{index}...")
        print(f"Original date: {test_case['timestamp']}")
        print(f"Number of goods: {test_case['num_goods']}")
        
        # Recreate the test case
        goods, players = failed_test_storage.recreate_test_case(test_case)
        
        # Run the test
        start_time = time.time()
        results = run_tests(goods, players)
        end_time = time.time()
        
        execution_time = end_time - start_time
        is_efx = results['algorithm']['is_efx']
        
        print(f"\nExecution time: {execution_time:.3f} seconds")
        print(f"Result: {'EFX' if is_efx else 'Still Not EFX'}")
        
        if is_efx:
            print("\n[+] This test case now passes! The algorithm has been improved.")
            confirm = input("Delete this test case since it now passes? (y/N): ")
            if confirm.lower() in ['y', 'yes']:
                failed_test_storage.delete_failed_test(index)
        else:
            print("\n[X] This test case still fails.")
        
        # Log the re-test with Phase 2 information
        log_message = f"RE_TEST: TestCase#{index}, EFX={is_efx}, Time={execution_time:.3f}s"
        
        # Add Phase 2 information
        phase2_info = results['algorithm']['phase2_info']
        if phase2_info['executed']:
            log_message += f", Phase2=YES, Steps={phase2_info['steps']}"
            log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
            log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
            if phase2_info['efx_achieved_in_phase2']:
                log_message += ", EFX_ViaPhase2=YES"
        else:
            log_message += ", Phase2=NO"
        
        write_log("efx_test_logs.txt", log_message)
        
        # Save Phase 2 test case if Phase 2 was executed
        if phase2_info['executed']:
            phase2_test_storage.save_phase2_test(goods, players, "retest", phase2_info)
        
    except ValueError:
        print("Please enter a valid number.")
    except Exception as e:
        print(f"Error running test: {e}")
    
    input("\nPress Enter to continue...")

def run_all_failed_tests():
    """Run all stored failed test cases."""
    count = failed_test_storage.get_failed_tests_count()
    print(f"\nRunning all {count} failed test cases...")
    
    passed_tests = []
    failed_tests = []
    total_time = 0
    
    for i in range(1, count + 1):
        print(f"\nRunning test case #{i}/{count}...")
        test_case = failed_test_storage.get_failed_test_by_index(i)
        
        if test_case is None:
            continue
        
        # Recreate and run the test case
        goods, players = failed_test_storage.recreate_test_case(test_case)
        start_time = time.time()
        results = run_tests(goods, players)
        end_time = time.time()
        
        execution_time = end_time - start_time
        total_time += execution_time
        is_efx = results['algorithm']['is_efx']
        
        if is_efx:
            passed_tests.append(i)
            print(f"[+] Test #{i}: Now EFX ({execution_time:.3f}s)")
        else:
            failed_tests.append(i)
            print(f"[X] Test #{i}: Still fails ({execution_time:.3f}s)")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("BATCH RE-TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {count}")
    print(f"Now passing: {len(passed_tests)}")
    print(f"Still failing: {len(failed_tests)}")
    print(f"Total execution time: {total_time:.3f} seconds")
    print(f"Average time per test: {total_time/count:.3f} seconds")
    
    if passed_tests:
        print(f"\nPassing tests: {passed_tests}")
        confirm = input("Delete all passing test cases? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            deleted = failed_test_storage.delete_multiple_failed_tests(passed_tests)
            print(f"Deleted {len(deleted)} test cases that now pass.")
    
    # Log the batch re-test
    log_message = f"BATCH_RE_TEST: Total={count}, Passed={len(passed_tests)}, Failed={len(failed_tests)}, TotalTime={total_time:.3f}s"
    write_log("efx_test_logs.txt", log_message)
    
    input("\nPress Enter to continue...")

def delete_specific_failed_test():
    """Delete a specific failed test case."""
    clear_terminal()
    print("=" * 60)
    print("DELETE SPECIFIC FAILED TEST")
    print("=" * 60)
    
    count = failed_test_storage.get_failed_tests_count()
    if count == 0:
        print("No failed test cases to delete.")
        input("\nPress Enter to continue...")
        return
    
    print("Current failed test cases:")
    failed_test_storage.print_failed_tests_summary()
    
    try:
        index = int(input(f"\nEnter test case number to delete (1-{count}): "))
        test_case = failed_test_storage.get_failed_test_by_index(index)
        
        if test_case is None:
            print("Invalid test case number.")
            input("Press Enter to continue...")
            return
        
        print(f"\nTest case #{index}:")
        print(f"Date: {test_case['timestamp']}")
        print(f"Goods: {test_case['num_goods']}")
        print(f"Mode: {test_case['test_mode']}")
        
        confirm = input("\nAre you sure you want to delete this test case? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            if failed_test_storage.delete_failed_test(index):
                print("Test case deleted successfully.")
            else:
                print("Failed to delete test case.")
        else:
            print("Deletion cancelled.")
    
    except ValueError:
        print("Please enter a valid number.")
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to continue...")

def delete_multiple_failed_tests():
    """Delete multiple failed test cases."""
    clear_terminal()
    print("=" * 60)
    print("DELETE MULTIPLE FAILED TESTS")
    print("=" * 60)
    
    count = failed_test_storage.get_failed_tests_count()
    if count == 0:
        print("No failed test cases to delete.")
        input("\nPress Enter to continue...")
        return
    
    print("Current failed test cases:")
    failed_test_storage.print_failed_tests_summary()
    
    print(f"\nEnter test case numbers to delete (1-{count})")
    print("Examples: '1,3,5' or '1 3 5' or '1-5' for range")
    indices_input = input("Test case numbers: ").strip()
    
    if not indices_input:
        print("No indices provided.")
        input("Press Enter to continue...")
        return
    
    try:
        # Parse different input formats
        indices = []
        
        # Handle range format (e.g., "1-5")
        if '-' in indices_input and ',' not in indices_input:
            parts = indices_input.split('-')
            if len(parts) == 2:
                start, end = int(parts[0]), int(parts[1])
                indices = list(range(start, end + 1))
        else:
            # Handle comma or space separated format
            if ',' in indices_input:
                indices = [int(x.strip()) for x in indices_input.split(',')]
            else:
                indices = [int(x.strip()) for x in indices_input.split()]
        
        # Filter valid indices
        valid_indices = [i for i in indices if 1 <= i <= count]
        invalid_indices = [i for i in indices if i not in valid_indices]
        
        if invalid_indices:
            print(f"Invalid indices (ignored): {invalid_indices}")
        
        if not valid_indices:
            print("No valid indices to delete.")
            input("Press Enter to continue...")
            return
        
        print(f"\nYou want to delete {len(valid_indices)} test cases: {valid_indices}")
        confirm = input("Are you sure? (y/N): ")
        
        if confirm.lower() in ['y', 'yes']:
            deleted = failed_test_storage.delete_multiple_failed_tests(valid_indices)
            print(f"Successfully deleted {len(deleted)} test cases.")
        else:
            print("Deletion cancelled.")
    
    except ValueError:
        print("Invalid input format. Please use numbers separated by commas or spaces.")
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to continue...")

def clear_all_failed_tests():
    """Clear all failed test cases."""
    clear_terminal()
    print("=" * 60)
    print("CLEAR ALL FAILED TESTS")
    print("=" * 60)
    
    count = failed_test_storage.get_failed_tests_count()
    if count == 0:
        print("No failed test cases to clear.")
        input("\nPress Enter to continue...")
        return
    
    print(f"This will delete ALL {count} failed test cases.")
    print("This action cannot be undone!")
    
    confirm = input("\nAre you sure you want to delete all failed tests? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        confirm2 = input("Type 'DELETE ALL' to confirm: ")
        if confirm2 == 'DELETE ALL':
            deleted_count = failed_test_storage.clear_all_failed_tests()
            print(f"Successfully deleted all {deleted_count} failed test cases.")
        else:
            print("Confirmation failed. Deletion cancelled.")
    else:
        print("Deletion cancelled.")
    
    input("\nPress Enter to continue...")

def phase2_tests_management():
    """Manage Phase 2 test cases."""
    while True:
        clear_terminal()
        print("=" * 60)
        print("PHASE 2 TESTS MANAGEMENT")
        print("=" * 60)
        print()
        
        count = phase2_test_storage.get_phase2_tests_count()
        print(f"Stored Phase 2 test cases: {count}")
        print()
        print("OPTIONS:")
        print("1. View all Phase 2 test cases")
        print("2. Run a specific Phase 2 test case")
        print("3. Run all Phase 2 test cases") 
        print("4. Delete specific Phase 2 test case")
        print("5. Delete multiple Phase 2 test cases")
        print("6. Clear all Phase 2 test cases")
        print("0. Back to main menu")
        print()
        print("=" * 60)
        
        choice = input("Select option (0-6): ").strip()
        
        if choice == "1":
            view_phase2_tests()
        elif choice == "2":
            run_specific_phase2_test()
        elif choice == "3":
            run_all_phase2_tests()
        elif choice == "4":
            delete_specific_phase2_test()
        elif choice == "5":
            delete_multiple_phase2_tests()
        elif choice == "6":
            clear_all_phase2_tests()
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")
            input("Press Enter to continue...")

def view_phase2_tests():
    """Display all stored Phase 2 test cases."""
    clear_terminal()
    print("=" * 60)
    print("PHASE 2 TEST CASES")
    print("=" * 60)
    
    phase2_test_storage.print_phase2_tests_summary()
    input("\nPress Enter to continue...")

def run_specific_phase2_test():
    """Run a specific Phase 2 test case."""
    clear_terminal()
    print("=" * 60)
    print("RUN SPECIFIC PHASE 2 TEST")
    print("=" * 60)
    
    count = phase2_test_storage.get_phase2_tests_count()
    if count == 0:
        print("No Phase 2 test cases available.")
        input("\nPress Enter to continue...")
        return
    
    print("Available Phase 2 test cases:")
    phase2_test_storage.print_phase2_tests_summary()
    
    try:
        index = int(input(f"\nEnter test case number to run (1-{count}): "))
        
        if not (1 <= index <= count):
            print("Invalid test case number.")
            input("Press Enter to continue...")
            return
        
        goods, players = phase2_test_storage.recreate_players_from_test(index)
        if not goods or not players:
            print("Error: Could not load test case.")
            input("Press Enter to continue...")
            return
        
        print(f"\nRunning Phase 2 test case #{index}...")
        phase2_test_storage.print_phase2_test_details(index)
        
        start_time = time.time()
        results = run_tests(goods, players)
        end_time = time.time()
        
        execution_time = end_time - start_time
        is_efx = results['algorithm']['is_efx']
        
        print(f"\nExecution time: {execution_time:.3f} seconds")
        print(f"Result: {'EFX' if is_efx else 'Still Not EFX'}")
        
        # Log the re-test with Phase 2 information
        log_message = f"PHASE2_RE_TEST: TestCase#{index}, EFX={is_efx}, Time={execution_time:.3f}s"
        
        # Add Phase 2 information
        phase2_info = results['algorithm']['phase2_info']
        if phase2_info['executed']:
            log_message += f", Phase2=YES, Steps={phase2_info['steps']}"
            log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
            log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
            if phase2_info['efx_achieved_in_phase2']:
                log_message += ", EFX_ViaPhase2=YES"
        else:
            log_message += ", Phase2=NO"
        
        write_log("efx_test_logs.txt", log_message)
        
        # Save Phase 2 test case if Phase 2 was executed
        if phase2_info['executed']:
            phase2_test_storage.save_phase2_test(goods, players, "phase2_retest", phase2_info)
        
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"Error running test case: {e}")
    
    input("\nPress Enter to continue...")

def run_all_phase2_tests():
    """Run all stored Phase 2 test cases."""
    clear_terminal()
    print("=" * 60)
    print("RUN ALL PHASE 2 TESTS")
    print("=" * 60)
    
    count = phase2_test_storage.get_phase2_tests_count()
    if count == 0:
        print("No Phase 2 test cases available.")
        input("\nPress Enter to continue...")
        return
    
    print(f"Running all {count} Phase 2 test cases...")
    
    phase2_again_count = 0
    efx_results = 0
    total_time = 0
    
    for i in range(1, count + 1):
        print(f"\nRunning test case {i}/{count}...")
        
        goods, players = phase2_test_storage.recreate_players_from_test(i)
        if not goods or not players:
            print(f"Error loading test case {i}")
            continue
        
        start_time = time.time()
        results = run_tests(goods, players)
        end_time = time.time()
        
        test_time = end_time - start_time
        total_time += test_time
        is_efx = results['algorithm']['is_efx']
        phase2_info = results['algorithm']['phase2_info']
        
        if is_efx:
            efx_results += 1
        
        if phase2_info['executed']:
            phase2_again_count += 1
        
        # Log individual result
        log_message = f"PHASE2_BATCH_RE_TEST: TestCase#{i}, EFX={is_efx}, Time={test_time:.3f}s"
        if phase2_info['executed']:
            log_message += f", Phase2=YES, Steps={phase2_info['steps']}"
            log_message += f", Improvements={'YES' if phase2_info['improvements_found'] else 'NO'}"
            log_message += f", EnvyReduction={phase2_info['envy_reduction']:.3f}"
            if phase2_info['efx_achieved_in_phase2']:
                log_message += ", EFX_ViaPhase2=YES"
        else:
            log_message += ", Phase2=NO"
        
        write_log("efx_test_logs.txt", log_message)
    
    # Summary
    print(f"\n" + "=" * 60)
    print("PHASE 2 BATCH RE-TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {count}")
    print(f"EFX results: {efx_results}")
    print(f"Tests entering Phase 2 again: {phase2_again_count}")
    print(f"Total execution time: {total_time:.3f} seconds")
    print(f"Average time per test: {total_time/count:.3f} seconds")
    
    # Log the batch re-test
    log_message = f"PHASE2_BATCH_RE_TEST: Total={count}, EFX={efx_results}, Phase2Again={phase2_again_count}, TotalTime={total_time:.3f}s"
    write_log("efx_test_logs.txt", log_message)
    
    input("\nPress Enter to continue...")

def delete_specific_phase2_test():
    """Delete a specific Phase 2 test case."""
    clear_terminal()
    print("=" * 60)
    print("DELETE SPECIFIC PHASE 2 TEST")
    print("=" * 60)
    
    count = phase2_test_storage.get_phase2_tests_count()
    if count == 0:
        print("No Phase 2 test cases to delete.")
        input("\nPress Enter to continue...")
        return
    
    print("Current Phase 2 test cases:")
    phase2_test_storage.print_phase2_tests_summary()
    
    try:
        index = int(input(f"\nEnter test case number to delete (1-{count}): "))
        test_case = phase2_test_storage.get_phase2_test(index)
        
        if test_case is None:
            print("Invalid test case number.")
            input("Press Enter to continue...")
            return
        
        print(f"\nTest case #{index}:")
        print(f"Date: {test_case['timestamp']}")
        print(f"Goods: {len(test_case['goods'])}")
        print(f"Mode: {test_case['test_mode']}")
        
        confirm = input("\nAre you sure you want to delete this test case? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            if phase2_test_storage.delete_phase2_test(index):
                print("Phase 2 test case deleted successfully.")
            else:
                print("Failed to delete test case.")
        else:
            print("Deletion cancelled.")
    
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to continue...")

def delete_multiple_phase2_tests():
    """Delete multiple Phase 2 test cases."""
    clear_terminal()
    print("=" * 60)
    print("DELETE MULTIPLE PHASE 2 TESTS")
    print("=" * 60)
    
    count = phase2_test_storage.get_phase2_tests_count()
    if count == 0:
        print("No Phase 2 test cases to delete.")
        input("\nPress Enter to continue...")
        return
    
    print("Current Phase 2 test cases:")
    phase2_test_storage.print_phase2_tests_summary()
    
    print(f"\nEnter test case numbers to delete (1-{count})")
    print("Examples: '1,3,5' or '1 3 5' or '1-5' for range")
    indices_input = input("Test case numbers: ").strip()
    
    if not indices_input:
        print("No test cases specified.")
        input("Press Enter to continue...")
        return
    
    try:
        indices = phase2_test_storage.parse_indices_input(indices_input)
        
        # Validate all indices
        invalid_indices = [i for i in indices if not (1 <= i <= count)]
        if invalid_indices:
            print(f"Invalid test case numbers: {invalid_indices}")
            input("Press Enter to continue...")
            return
        
        print(f"\nYou are about to delete {len(indices)} test cases: {indices}")
        confirm = input("Are you sure? (y/N): ")
        
        if confirm.lower() in ['y', 'yes']:
            deleted_count = phase2_test_storage.delete_multiple_phase2_tests(indices)
            print(f"Successfully deleted {deleted_count} Phase 2 test cases.")
        else:
            print("Deletion cancelled.")
    
    except ValueError as e:
        print(f"Invalid input format: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to continue...")

def clear_all_phase2_tests():
    """Clear all Phase 2 test cases."""
    clear_terminal()
    print("=" * 60)
    print("CLEAR ALL PHASE 2 TESTS")
    print("=" * 60)
    
    count = phase2_test_storage.get_phase2_tests_count()
    if count == 0:
        print("No Phase 2 test cases to clear.")
        input("\nPress Enter to continue...")
        return
    
    print(f"This will delete ALL {count} Phase 2 test cases.")
    print("This action cannot be undone!")
    
    confirm = input("\nAre you sure you want to delete all Phase 2 tests? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        confirm2 = input("Type 'DELETE ALL' to confirm: ")
        if confirm2 == 'DELETE ALL':
            phase2_test_storage.clear_all_phase2_tests()
            print(f"Successfully deleted all {count} Phase 2 test cases.")
        else:
            print("Confirmation failed. Deletion cancelled.")
    else:
        print("Deletion cancelled.")
    
    input("\nPress Enter to continue...")

def configuration_settings():
    """Manage configuration settings."""
    while True:
        clear_terminal()
        print("=" * 60)
        print("CONFIGURATION SETTINGS")
        print("=" * 60)
        print()
        print("CURRENT SETTINGS:")
        print()
        
        # Show key settings
        print(f"Normalization target: {config.get('algorithm.normalization.target')}")
        print(f"Tie tolerance: {config.get('algorithm.phase_1a.tie_tolerance')}")
        print(f"Max sacrifice threshold: {config.get('algorithm.phase_1a.max_sacrifice_threshold')}")
        print(f"Top options to consider: {config.get('algorithm.phase_1a.top_options_to_consider')}")
        print(f"Valuation range: {config.get('testing.valuation_range.min')}-{config.get('testing.valuation_range.max')}")
        print(f"Base epsilon for perturbation: {config.get('testing.perturbation.base_epsilon')}")
        print()
        print("OPTIONS:")
        print("1. Show full configuration")
        print("2. Modify tie tolerance")
        print("3. Modify sacrifice threshold")
        print("4. Modify valuation range")
        print("5. Reload configuration from file")
        print("6. Save current configuration")
        print("0. Back to main menu")
        print()
        print("=" * 60)
        
        try:
            choice = input("Select an option (0-6): ").strip()
            
            if choice == "1":
                show_full_configuration()
            elif choice == "2":
                modify_tie_tolerance()
            elif choice == "3":
                modify_sacrifice_threshold()
            elif choice == "4":
                modify_valuation_range()
            elif choice == "5":
                reload_configuration()
            elif choice == "6":
                save_configuration()
            elif choice == "0":
                break
            else:
                print("Invalid option. Please select 0-6.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to continue...")

def show_full_configuration():
    """Display the complete configuration."""
    clear_terminal()
    config.show_current_config()
    input("\nPress Enter to continue...")

def modify_tie_tolerance():
    """Modify the tie tolerance setting."""
    current = config.get('algorithm.phase_1a.tie_tolerance')
    print(f"\nCurrent tie tolerance: {current}")
    print("Recommended values: 0.001 (strict), 0.01 (normal), 0.1 (loose)")
    
    try:
        new_value = float(input("Enter new tie tolerance: "))
        if 0 <= new_value <= 1:
            config.update('algorithm.phase_1a.tie_tolerance', new_value)
            print(f"Tie tolerance updated to {new_value}")
        else:
            print("Value must be between 0 and 1")
    except ValueError:
        print("Invalid input. Please enter a number.")
    
    input("Press Enter to continue...")

def modify_sacrifice_threshold():
    """Modify the maximum sacrifice threshold."""
    current = config.get('algorithm.phase_1a.max_sacrifice_threshold')
    print(f"\nCurrent max sacrifice threshold: {current}")
    print("Recommended values: 0.1 (10%), 0.2 (20%), 0.3 (30%)")
    
    try:
        new_value = float(input("Enter new sacrifice threshold (0.0-1.0): "))
        if 0 <= new_value <= 1:
            config.update('algorithm.phase_1a.max_sacrifice_threshold', new_value)
            print(f"Sacrifice threshold updated to {new_value}")
        else:
            print("Value must be between 0 and 1")
    except ValueError:
        print("Invalid input. Please enter a number.")
    
    input("Press Enter to continue...")

def modify_valuation_range():
    """Modify the valuation range for random test generation."""
    current_min = config.get('testing.valuation_range.min')
    current_max = config.get('testing.valuation_range.max')
    print(f"\nCurrent valuation range: {current_min}-{current_max}")
    
    try:
        new_min = int(input("Enter new minimum valuation: "))
        new_max = int(input("Enter new maximum valuation: "))
        
        if new_min >= 1 and new_max > new_min:
            config.update('testing.valuation_range.min', new_min)
            config.update('testing.valuation_range.max', new_max)
            print(f"Valuation range updated to {new_min}-{new_max}")
        else:
            print("Invalid range. Min must be >= 1 and max must be > min.")
    except ValueError:
        print("Invalid input. Please enter integers.")
    
    input("Press Enter to continue...")

def reload_configuration():
    """Reload configuration from file."""
    try:
        config.reload()
        print("Configuration reloaded successfully!")
    except Exception as e:
        print(f"Error reloading configuration: {e}")
    
    input("Press Enter to continue...")

def save_configuration():
    """Save current configuration to file."""
    try:
        config.save()
        print("Configuration saved successfully!")
    except Exception as e:
        print(f"Error saving configuration: {e}")
    
    input("Press Enter to continue...")

def main():
    """Main function with interactive terminal interface."""
    # Initialize log file
    write_log("efx_test_logs.txt", "=== EFX TESTING SESSION STARTED ===")
    
    while True:
        show_menu()
        
        try:
            choice = input("Select an option (0-8): ").strip()
            
            if choice == "1":
                single_test_mode()
            elif choice == "2":
                continuous_test_mode()
            elif choice == "3":
                manual_test_mode()
            elif choice == "4":
                view_logs()
            elif choice == "5":
                clear_logs()
            elif choice == "6":
                failed_tests_management()
            elif choice == "7":
                phase2_tests_management()
            elif choice == "8":
                configuration_settings()
            elif choice == "0":
                clear_terminal()
                print("=" * 60)
                print("Thank you for using EFX Testing!")
                print("=" * 60)
                write_log("efx_test_logs.txt", "=== EFX TESTING SESSION ENDED ===")
                break
            else:
                clear_terminal()
                print("Invalid option. Please select 0-8.")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            clear_terminal()
            print("\nGoodbye!")
            write_log("efx_test_logs.txt", "=== EFX TESTING SESSION INTERRUPTED ===")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()