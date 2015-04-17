#!/usr/bin/env python

import sys, os, os.path

# Get GOTM-GUI directory from environment.
if 'GOTMGUIDIR' in os.environ:
    relguipath = os.environ['GOTMGUIDIR']
elif 'GOTMDIR' in os.environ:
    relguipath = os.path.join(os.environ['GOTMDIR'],'gui.py')
else:
    print 'Cannot find GOTM-GUI directory. Please set environment variable "GOTMDIR" to the GOTM root (containing gui.py), or "GOTMGUIDIR" to the GOTM-GUI root, before running.'
    sys.exit(1)

# Add the GOTM-GUI directory to the search path and import the common
# GOTM-GUI module (needed for command line parsing).
gotmguiroot = os.path.join(os.path.dirname(os.path.realpath(__file__)),relguipath)
sys.path.append(gotmguiroot)

import core.common,core.scenario,xmlstore.xmlstore

def main():
    import optparse
    parser = optparse.OptionParser(usage = 'usage: %prog [options] SCHEMAPATH NAMELISTDIRECTORY OUTPUTPATH',description='Converts a directory with namelist files (NAMELISTDIRECTORY) into an XML-based values file (OUTPUTPATH), using an XML-based schema that describes the namelist structure. The path to the schema (SCHEMAPATH) may point to a single schema file, or to a directory with schemas (and other metadata such as converters, default values). In the latter case, the program will try to auto-detect the newest applicable schema, and then convert the values to the desired version (see --targetversion option) if that is specified.')
    parser.add_option('--targetversion',type='string',help='Desired version to be used for the exported values file. If needed, values will be converted from the namelist version to this desired version. Note that this argument is only used if the provided SCHEMAPATH is a directory.')
    parser.add_option('--root',type='string',help='Schema node to be used as root. By specifying this, a subset of the schema can be converted (e.g., a single namelist file).')
    parser.add_option('-q','--quiet', action='store_true', help='Suppress output of progress messages')
    parser.add_option('-e','--export', choices=('xml','dir','zip'), help='Output type: xml = XML-based values file [default], dir = directory with XML-based values file and associated data, zip = zip file with XML-based values file and associated data.')
    parser.set_defaults(quiet=False,targetversion=None,root=None,export='xml')
    (options, args) = parser.parse_args()

    if len(args)<3:
        print '3 arguments required:\n- path to the schema file.\n- path to the directory with namelists.\n- path to save the XML values file to.'
        return 2

    # Get command line arguments
    schemapath = os.path.abspath(args.pop(0))
    nmlpath    = os.path.abspath(args.pop(0))
    targetpath = os.path.abspath(args.pop(0))

    # Check if the source path exists.
    if not os.path.exists(schemapath):
        print 'Error! The schema path "%s" does not exist.' % schemapath
        return 1
    if not os.path.exists(nmlpath):
        print 'Source path "%s" does not exist.' % nmlpath
        return 1
        
    if not options.quiet: core.common.verbose = True
    
    # Add custom GOTM data types if possible.
    try:
        import xmlstore.datatypes,xmlplot.data
        xmlstore.datatypes.register('gotmdatafile',xmlplot.data.LinkedFileVariableStore)
    except ImportError:
        pass

    if os.path.isfile(schemapath):
        # A single schema file is specified.
        if options.targetversion is not None:
            print '--targetversion argument is only used if the schema path is a directory. When it is a file, the exported values will always have the version of the specified schema.'
            return 2
        scen = core.scenario.NamelistStore(schemapath)
        scen.loadFromNamelists(nmlpath,strict=False,root=options.root)
    else:
        # A directory with one or more schema files (and potentially converters) is specified.
        class Scenario(core.scenario.NamelistStore):
            @classmethod
            def getSchemaInfo(cls):
                return xmlstore.xmlstore.schemainfocache[schemapath]
        try:
            scen = Scenario.fromNamelists(nmlpath,targetversion=options.targetversion,root=options.root)
        except Exception,e:
            raise
            print 'Could not find a schema that matches the namelists. Details:\n%s' % e
            return 1

    # Export to scenario.
    if not options.quiet: print 'Saving values to "%s"...' % targetpath
    if options.export=='xml':
        scen.save(targetpath)
    else:
        scen.saveAll(targetpath,targetisdir=options.export=='dir')

    # Clean-up (delete temporary directories etc.)
    scen.release()
    
    return 0

# If the script has been run (as opposed to imported), enter the main loop.
if (__name__=='__main__'):
    ret = main()
    sys.exit(ret)
