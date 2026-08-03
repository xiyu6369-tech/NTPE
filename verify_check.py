from core.knowledge.compatibility import verify_package

report = verify_package('artifacts/knowledge_packages/v1')
print('Overall:', 'PASS' if report.overall_passed else 'FAIL')
for r in report.results:
    print(f'  {r.check_name}: {"OK" if r.passed else "FAIL"} - {r.detail}')