'''
List of Views:
- DASHBOARD PAGE: Has a dashboard with stats.
- PROBLEM PAGE: Has the list of problems with sorting & paginations.
- DEESCRIPTION PAGE: Shows problem description of left side and has a text editor on roght side with code submit buttton.
'''
import traceback
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

from USERS.models import User, Submission
from OJ.models import Problem, TestCase
from OJ.forms import CodeForm
from datetime import datetime
from time import time

import os
import signal
import subprocess
import os.path
import docker


###############################################################################################################################


# To show stats in dashboards
@login_required(login_url='login')
def dashboardPage(request):
    total_ques_count = len(Problem.objects.all())
    easy_ques_count = len(Problem.objects.filter(difficulty="Easy"))
    medium_ques_count = len(Problem.objects.filter(difficulty="Medium"))
    tough_ques_count = len(Problem.objects.filter(difficulty="Tough"))

    user = request.user
    easy_solve_count = user.easy_solve_count
    medium_solve_count = user.medium_solve_count
    tough_solve_count = user.tough_solve_count
    total_solve_count = user.total_solve_count
    
    if easy_ques_count!=0:
          easy_progress = (easy_solve_count/easy_ques_count)*100
    else:
          easy_progress=0

    if medium_ques_count!=0:
        medium_progress = (medium_solve_count/medium_ques_count)*100
    else:
        medium_progress=0

    if tough_ques_count!=0:
        tough_progress = (tough_solve_count/tough_ques_count)*100
    else:
        tough_progress=0

    if total_ques_count!=0:
        total_progress = (total_solve_count/total_ques_count)*100
    else:
        total_progress=0

    context = {"easy_progress":easy_progress,"medium_progress":medium_progress,
                "tough_progress":tough_progress,"total_progress":total_progress,
                "easy_solve_count":easy_solve_count, "medium_solve_count":medium_solve_count, 
                "tough_solve_count":tough_solve_count,"total_solve_count":total_solve_count,
                "easy_ques_count":easy_ques_count, "medium_ques_count":medium_ques_count, 
                "tough_ques_count":tough_ques_count,"total_ques_count":total_ques_count}
    return render(request, 'dashboard.html', context)



###############################################################################################################################


# Has the list of problems with sorting & paginations
@login_required(login_url='login')
def problemPage(request):
    problems = Problem.objects.all()
    submissions = Submission.objects.filter(user=request.user, verdict="Accepted")
    accepted_problems = []
    for submission in submissions:
        accepted_problems.append(submission.problem_id)
    context = {'problems': problems, 'accepted_problems': accepted_problems}
    return render(request, 'problem.html', context)



###############################################################################################################################


# Shows problem description of left side and has a text editor on roght side with code submit buttton.
@login_required(login_url='login')
def descriptionPage(request, problem_id):
    user_id = request.user.id
    problem = get_object_or_404(Problem, id=problem_id)
    user = User.objects.get(id=user_id)
    form = CodeForm()
    context = {'problem': problem, 'user': user, 'user_id': user_id, 'code_form': form}
    return render(request, 'description.html', context)


###############################################################################################################################




def compile_code(container_name, compile_command):
    # Run the compilation command inside the Docker container
    result = subprocess.run(f"docker exec {container_name} {compile_command}", capture_output=True, shell=True)
    return result.returncode == 0, result.stderr.decode("utf-8")


def run_code(container_name, execution_command, input_data, timeout):
    # Run the user code with the provided input inside the Docker container
    try:
        result = subprocess.run(
            f"docker exec {container_name} sh -c 'echo \"{input_data}\" | {execution_command}'",
            capture_output=True,
            timeout=timeout,
            shell=True,
            text=True
        )
        return True, result.stdout.strip(), None
    except subprocess.TimeoutExpired:
        return False, None, "Time Limit Exceeded"
    except Exception as e:
        traceback.print_exc()
        return False, None, "Runtime Error"


@login_required(login_url='login')
def verdictPage(request, problem_id):
    if request.method == 'POST':
        # Setting docker-client
        docker_client = docker.from_env()
        Running = "running"

        problem = get_object_or_404(Problem, id=problem_id)
        testcase = get_object_or_404(TestCase, problem_id=problem_id)
        testcase.output = testcase.output.replace('\r\n', '\n').strip()  # Replace line endings for comparison

        # Score of a problem
        if problem.difficulty == "Easy":
            score = 10
        elif problem.difficulty == "Medium":
            score = 30
        else:
            score = 50

        # Default verdict is "Wrong Answer"
        verdict = "Wrong Answer"
        run_time = 0

        # Extract data from the form
        form = CodeForm(request.POST)
        user_code = ''
        if form.is_valid():
            user_code = form.cleaned_data.get('user_code')
            user_code = user_code.replace('\r\n', '\n').strip()

        language = request.POST['language']
        submission = Submission(
            user=request.user,
            problem=problem,
            submission_time=datetime.now(),
            language=language,
            user_code=user_code
        )
        submission.save()

        filename = str(submission.id)

        # Language-specific configurations
        if language == "C++":
            extension = ".cpp"
            container_name = "oj-cpp"
            compile_command = f"g++ -o {filename} {filename}.cpp"
            execution_command = f"./{filename}"
            docker_img = "gcc:11.2.0"

        elif language == "Python3":
            extension = ".py"
            container_name = "oj-py3"
            compile_command = "echo ''"  # No need to compile Python code
            execution_command = f"python {filename}.py"
            docker_img = "python3"

        # File and Docker container configurations
        file = filename + extension
        filepath = os.path.join(settings.FILES_DIR, file)

        # Write the user code to the file
        with open(filepath, "w") as code:
            code.write(user_code)

        # Check if the Docker container is running, start if not found
        try:
            container = docker_client.containers.get(container_name)
            container_state = container.attrs['State']
            container_is_running = container_state['Status'] == Running
            if not container_is_running:
                subprocess.run(f"docker start {container_name}", shell=True)
        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {container_name} {docker_img}", shell=True)

        # Copy the file to the Docker container
        subprocess.run(f"docker cp {filepath} {container_name}:/{file}", shell=True)

        # Compile the code
        compiled_successfully, compile_error_msg = compile_code(container_name, compile_command)
        if not compiled_successfully:
            verdict = "Compilation Error"

        else:
            # Run the code on the given input and take the output
            start_time = time()
            execution_successful, user_stdout, run_error_msg = run_code(container_name, execution_command,
                                                                        testcase.input, problem.time_limit)
            run_time = time() - start_time

            # Remove the compiled binary or Python script from the container
            subprocess.run(f"docker exec {container_name} rm {file}", shell=True)

            if not execution_successful:
                verdict = run_error_msg

            elif user_stdout.strip() == testcase.output.strip():
                verdict = "Accepted"

        # Clean up the file after running
        os.remove(filepath)

        # Handling leaderboard and other score-related operations (as before)

        context = {'verdict': verdict}
        return render(request, 'verdict.html', context)
