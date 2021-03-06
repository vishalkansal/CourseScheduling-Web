from CourseScheduling.blueprints.schedule.models import Course, Requirement, Major, Quarter
import lib.CourseSchedulingAlgorithm as cs
import warnings
import logging

def getCourse(dept, cid):
    c = Course.objects(dept=dept, cid=cid).first()
    return cs.Course(name=c.name, units=c.units, quarter_codes=c.quarters,
                     prereq=c.prereq, is_upper_only=c.upperOnly)


def getMajorsNames():
    """
    :return:  list of major names
    """
    return [m.name for m in Major.objects()]

def getMajorModel():
    """
    :return: all majors with their information defined in models.py
    """
    return list(Major.objects())


def getMajorReqNspecs(major):
    """
    :param major: should be the model defined in models.py
    :return:
    """
    if major:
        return major.requirements, major.specs
    return [], []

def getMajorReqNspecsByName(major_name):
    """
    :param major_name: name of the major
    :return: a list of major requirements, and a list of major sepcs
    """
    m = Major.objects(name=major_name)
    if m.first():
        return m.first().requirements, m.first().specs
    return [],[]


def getMajorRequirementsByName(major_name):
    """
    :param major_name: name of the major
    :return: a list of major requirements, (requirement is defined in models.py)
    """
    m = Major.objects(name=major_name)
    if m.first():
        return m.first().requirements
    return []

def getMajorSpecsByName(major_name):
    """
    :param major_name: name of the major
    :return: a list of major specs, (spec is also a requirement defined in models.py)
    """
    m = Major.objects(name=major_name)
    if m.first():
        return m.first().specs
    return []

# temporary 
def getAllSpecs():
    specs = []
    for major in Major.objects():
        specs.extend([s.name for s in major.specs])
    return specs

def getQuarterCodes():
    """
    :return:
    """
    quarters = Quarter.objects()
    return [(q.code, q.name) for q in quarters]

def getInfo(req):
    G, R, R_detail = dict(), dict(), dict()
    for r in req:
        R[r] = list()
        R_detail[r] = list()
        if Requirement.objects(name=r).first() == None:
            warnings.warn(r + "not exist")
            continue

        for subr in Requirement.objects(name=r).first().sub_reqs:
            c_set = set()
            R[r].append(subr.req_num)
            for c in subr.req_list:
                c_name = c.dept + " " + c.cid
                c_set.add(c_name)
                G[c_name] = cs.Course(name=c.name, units=c.units,
                                      quarter_codes=convert_quarters(c.quarters),
                                      prereq=convert_prereq(c.prereq),
                                      is_upper_only=c.upperOnly,
                                      priority=c.priority)
            R_detail[r].append(c_set)
    return G, R, R_detail

def getSchedule(upper_units = 90, \
    max_widths = {0: 13, 'else': 16}, \
    startQ = 0, \
    avoid = set(), \
    taken = set(), \
    spec = [], \
    ge_filter = {}, \
    majors = []):

    G, R, R_detail = dict(), dict(), dict()
    for mname in majors:
        major = Major.objects(name=mname.upper()).first()
        if not major:
            continue
        g, r, r_detail = major.prepareScheduling(spec=spec, ge_filter=ge_filter)
        G.update(g)
        R.update(r)
        R_detail.update(r_detail)

    # update requirement table based on the taken information
    cs.update_requirements(R_detail, R, taken)
    # construct CourseGraph. graph is labeled after init
    graph = cs.CourseGraph(G, r_detail=R_detail, R=R, avoid=avoid, taken=taken)
    # construct Schedule with width func requirements
    L = cs.Schedule(widths=max_widths)
    # construct the scheduling class
    generator = cs.Scheduling(start_q=startQ)
    # get the best schedule when the upper bound ranges from 0 to 10, inclusive.
    L, best_u, best_r = generator.get_best_schedule(graph, L, R, 0, 10)

    max_row_length = max(len(row) for row in L.L)

    # the parameters for render_template will be provided by CourseSchedulingAlgorithm:
    #   1,  L : best schedule generated by the algorithm
    #   2,  max_row_length : the max length of a row in this schedule

    return L, max_row_length

def convert_prereq(prereq):
    output = []
    for or_set in prereq:
        output.append([])
        for course in or_set:
            output[-1].append(course.dept + " " + course.cid)
    return output


def convert_quarters(quarters):
    for idx, q in enumerate(quarters):
        quarters[idx] = q.code
    return quarters
