import unittest

from project.services.classification import classify_department_and_priority


class ClassificationTests(unittest.TestCase):
    def test_sanitation_and_high_priority(self):
        department, priority = classify_department_and_priority('Garbage waste near road')
        self.assertEqual(department, 'Sanitation Department')
        self.assertEqual(priority, 'High')

    def test_urgent_overrides_priority(self):
        department, priority = classify_department_and_priority('Street light issue urgent safety')
        self.assertEqual(department, 'Electricity Department')
        self.assertEqual(priority, 'High')


if __name__ == '__main__':
    unittest.main()
