# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Create a test employee the way 19.0 tests do, on 18.0.

19.0 delegates ``hr.employee`` to ``hr.version``, so one ``create()`` carrying
``date_version`` / ``contract_date_start`` / ``wage`` / ``struct_id`` gives an
employee with a running contract. 18.0 has no delegation: the contract is a
separate ``hr.contract`` and must be created in state ``open`` for
``employee.contract_id`` to resolve. ``create_employee`` splits the values and
does that, so a test ported from 19.0 keeps its data as written.
"""

#: 19.0 names of hr.version fields -> 18.0 hr.contract names.
RENAMED = {
    "contract_date_start": "date_start",
    "contract_date_end": "date_end",
}
#: 19.0-only keys with no 18.0 counterpart.
DROPPED = {"date_version"}
#: Fields both models have that the contract must carry too.
SHARED = {"resource_calendar_id", "company_id"}


def split_contract_vals(employee_model, vals):
    """(employee values, contract values) from 19.0-style employee values."""
    contract_model = employee_model.env["hr.contract"]
    emp, con = {}, {}
    for key, value in vals.items():
        if key in DROPPED:
            continue
        key = RENAMED.get(key, key)
        efield = employee_model._fields.get(key)
        on_contract = key in contract_model._fields and (
            efield is None
            or (efield.related or "").startswith("contract_id.")
            or key in ("date_start", "date_end"))
        if on_contract:
            con[key] = value
        else:
            emp[key] = value
        if key in SHARED and key in contract_model._fields:
            con[key] = value
    return emp, con


def create_employee(employee_model, vals, contract_state="open"):
    """Create the employee and, when *vals* carry contract data, its contract."""
    emp_vals, con_vals = split_contract_vals(employee_model, vals)
    employee = employee_model.create(emp_vals)
    if set(con_vals) - SHARED:
        con_vals.setdefault("name", "Contract %s" % employee.name)
        con_vals.setdefault("wage", 0.0)
        if "date_start" not in con_vals:
            con_vals["date_start"] = "2000-01-01"
        con_vals["employee_id"] = employee.id
        con_vals.setdefault("state", contract_state)
        employee_model.env["hr.contract"].with_company(
            employee.company_id).create(con_vals)
    return employee


def _contract_vals(employee, vals):
    env = employee.env
    out = {}
    for key, value in vals.items():
        if key in DROPPED:
            continue
        key = RENAMED.get(key, key)
        if key in env["hr.contract"]._fields:
            out[key] = value
    return out


def write_contract(employee, vals, contract_state="open"):
    """19.0's ``employee.version_id.write(vals)`` on 18.0: write the running
    contract, creating it first when the employee has none. Returns it."""
    contract = employee.contract_id
    cvals = _contract_vals(employee, vals)
    if contract:
        contract.write(cvals)
        return contract
    cvals.setdefault("name", "Contract %s" % employee.name)
    cvals.setdefault("wage", 0.0)
    cvals.setdefault("date_start", "2000-01-01")
    cvals.setdefault("resource_calendar_id", employee.resource_calendar_id.id)
    cvals.update(employee_id=employee.id, state=contract_state)
    return employee.env["hr.contract"].with_company(employee.company_id).create(cvals)


def add_contract(employee, vals, contract_state="open"):
    """19.0's ``employee.create_version(vals)`` on 18.0: a further contract,
    copying the current one's terms (19.0 copies the version)."""
    current = employee.contract_id or employee.with_context(
        active_test=False).contract_ids.sorted("date_start")[-1:]
    cvals = current.copy_data()[0] if current else {}
    cvals.update(_contract_vals(employee, vals))
    cvals.update(employee_id=employee.id, state=contract_state)
    cvals.setdefault("name", "Contract %s" % employee.name)
    return employee.env["hr.contract"].with_company(employee.company_id).create(cvals)


def write_version(employee, vals):
    """19.0's ``employee.version_id.write(vals)`` where *vals* may hold fields
    19.0 keeps on the version but 18.0 on the employee (``address_id``): the
    contract's fields go to the contract, the rest to the employee."""
    contract_fields = employee.env["hr.contract"]._fields
    cvals, evals = {}, {}
    for key, value in vals.items():
        if key in DROPPED:
            continue
        key = RENAMED.get(key, key)
        efield = employee._fields.get(key)
        if key in contract_fields and not (
                efield and not (efield.related or "").startswith("contract_id.")):
            cvals[key] = value
        else:
            evals[key] = value
    if evals:
        employee.write(evals)
    return write_contract(employee, cvals) if cvals else employee.contract_id
