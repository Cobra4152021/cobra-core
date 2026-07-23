# Cleanup checklist

- [ ] Stop qualification processes
- [ ] Terminate GPU instance
- [ ] Delete temporary volumes (unless retention authorized)
- [ ] Delete temporary object-storage uploads
- [ ] Revoke temporary credentials
- [ ] Confirm no managed endpoint / recurring job / unauthorized snapshot
- [ ] Update `evaluations/cloud/cleanup-verification.json`
- [ ] Update `evaluations/cloud/cost-record.json`
