class MockCrewAIEnterpriseAPI:
    def get_crew_recommendation(self, task):
        return {
            "status": "success",
            "crew": [
                {"role": "Analyst", "expertise": "Data Analysis"},
                {"role": "Developer", "expertise": "Python"}
            ],
            "confidence_score": 0.95
        }

    def execute_task(self, task_description):
        return {
            "status": "completed",
            "result": f"Mocked execution result for: {task_description}",
            "execution_time": "2.5s"
        }
