# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .forms import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from .models import Alias





# -------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------- #
#
#                                            Create your views here  
#
# -------------------------------------------------------------------------------------------------- #
@login_required
def alias(request, pk_bundle):
    print ' \n\n \n\n-------------------------------------------------------------------------'
    print '\n\n---------------------- Add an Alias with ELSA ---------------------------'
    print '------------------------------ DEBUGGER ---------------------------------'

    # Get Bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        # ELSA's current user is the bundle user so begin view logic
        # Get forms
        form_alias = AliasForm(request.POST or None)

        # Declare context_dict for templating language used in ELSAs templates
        context_dict = {
            'form_alias':form_alias,
            'bundle':bundle,

        }

        # After ELSAs friend hits submit, if the forms are completed correctly, we should enter
        # this conditional.
        print '\n\n------------------------------- ALIAS INFO --------------------------------'
        if form_alias.is_valid():
            print 'form_alias is valid'
            # Create Alias model object
            alias = form_alias.save(commit=False)
            alias.bundle = bundle
            alias.save()
            print 'Alias model object: {}'.format(alias)

            # Find appropriate label(s).
            # Alias gets added to all Product_Bundle & Product_Collection labels.
            # We first get all labels of these given types except those in the Data collection which
            # are handled different from the other collections.
            all_labels = []
            product_bundle = Product_Bundle.objects.get(bundle=bundle)
            product_collections_list = Product_Collection.objects.filter(bundle=bundle).exclude(collection='Data')
            # We need to check for Product_Collections associated with Data products now.
                    
            all_labels.append(product_bundle)
            all_labels.extend(product_collections_list)

            for label in all_labels:
                # Open appropriate label(s).  
                print '- Label: {}'.format(label)
                print ' ... Opening Label ... '
                label_list = open_label(label.label())
                label_object = label_list[0]
                label_root = label_list[1]
                # Build Alias
                print ' ... Building Label ... '
                label_root = alias.build_alias(label_root)
		#alias.alias_list.append(label_root)


                # Close appropriate label(s)
                print ' ... Closing Label ... '
                close_label(label_object, label_root)

            #print alias.print_alias_list()

            print '---------------- End Build Alias -----------------------------------'  
	

        # Get all current Alias objects associated with the user's Bundle
        alias_list = Alias.objects.filter(bundle=bundle)
        context_dict['alias_list'] = alias_list
        return render(request, 'build/alias/alias.html',context_dict)
    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')









@login_required
def alias_delete(request, pk_bundle, alias):

    print ' \n\n \n\n-------------------------------------------------------------------------'
    print '\n\n---------------------- Remove an Alias with ELSA ---------------------------'
    print '------------------------------ DEBUGGER ---------------------------------'

    bundle = Bundle.objects.get(pk=pk_bundle)

    if request.user == bundle.user:
	print "authorized user"
        delete_alias = request.POST.get('Delete')


        context_dict = {
	    'alias':alias,
  	    'bundle':bundle,
	    'delete_alias':delete_alias,
        }

        print alias
        print request
        print bundle
    
        alias_class = Alias()

        if request.method == 'POST':
	    alias_class.remove(bundle, alias)
	    alias_to_remove = Alias.objects.filter(bundle=bundle).filter(alternate_id=alias)
	    alias_to_remove.delete()
	    return redirect('build:alias', pk_bundle = pk_bundle)

        return render(request, 'build/alias_delete/alias_delete.html',context_dict)

    else:
	print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')














"""
    build is the start of the bundle building process.  Because a bundle has yet to be created, there is
    no security check to see if the user is associated with the bundle...
"""
@login_required
def build(request): 
    print ' \n\n \n\n-------------------------------------------------------------------------'
    print '\n\n---------------- Welcome to Build A Bundle with ELSA --------------------'
    print '------------------------------ DEBUGGER ---------------------------------'


    # Get forms
    form_bundle = BundleForm(request.POST or None)
    form_collections = CollectionsForm(request.POST or None)

    # Declare context_dict for template
    context_dict = {
        'form_bundle':form_bundle,
        'form_collections':form_collections,
        'user':request.user,
    }

    print '\n\n------------------------------- USER INFO -------------------------------'
    print 'User:    {}'.format(request.user)
    print 'Agency:  {}'.format(request.user.userprofile.agency)
    print 'All users have access to this area.'


    print '\n\n------------------------------- BUILD INFO --------------------------------'
    print '\n ... waiting on user input ...\n'
    # After ELSAs friend hits submit, if the forms are completed correctly, we should enter here
    # this conditional.
    if form_bundle.is_valid() and form_collections.is_valid():
        print 'form_bundle and form_collections are valid'

        # Check Uniqueness  --- GOTTA BE A BETTER WAY (k)
        bundle_name = form_bundle.cleaned_data['name']
        bundle_user = request.user
        bundle_count = Bundle.objects.filter(name=bundle_name, user=bundle_user).count()
        # If user and bundle name are unique, then...
        if bundle_count == 0:

            # Create Bundle model.
            bundle = form_bundle.save(commit=False)
	    bundle.uniqueifier = bundle.name + "_" + str(request.user.id)
            bundle.user = request.user
            bundle.status = 'b' # b for build.  New Bundles are always in build stage first.
            bundle.save()
            print 'Bundle model object: {}'.format(bundle)

            # Build PDS4 Ccmpliant Bundle directory in User Directory.
            bundle.build_directory()
            print 'Bundle directory: {}'.format(bundle.directory())

            # Create Product_Bundle model.
            product_bundle = ProductBundleForm().save(commit=False)
            product_bundle.bundle = bundle
            product_bundle.save()
            print 'product_bundle model object: {}'.format(product_bundle)

            # Build Product_Bundle label using the base case template found in
            # templates/pds4/basecase
            print '\n---------------Start Build Product_Bundle Base Case------------------------'
            product_bundle.build_base_case()  # simply copies baseecase to user bundle directory
            # Open label - returns a list where index 0 is the label object and 1 is the tree
            print ' ... Opening Label ... '
            label_list = open_label(product_bundle.label()) #list = [label_object, label_root]
            label_object = label_list[0]
            label_root = label_list[1]
            # Fill label - fills 
            print ' ... Filling Label ... '
            label_root = product_bundle.fill_base_case(label_root)
            # Close label
            print ' ... Closing Label ... '
            close_label(label_object, label_root)           
            print '---------------- End Build Product_Bundle Base Case -------------------------'
  
            # Create Collections Model Object and list of Collections, list of Collectables
            collections = form_collections.save(commit=False)
            collections.bundle = bundle
            collections.save()
            print '\nCollections model object:    {}'.format(collections)
            
            # Create PDS4 compliant directories for each collection within the bundle.            
            collections.build_directories()

            # Each collection in collections needs a model and a label
            for collection in collections.list():

                # Create Product_Collection model for each collection
                product_collection = ProductCollectionForm().save(commit=False)
                product_collection.bundle = bundle
                if collection == 'document':
                    product_collection.collection = 'Document'
                elif collection == 'context':
                    product_collection.collection = 'Context'
                elif collection == 'xml_schema':
                    product_collection.collection = 'XML_Schema'
                elif collection == 'data':
                    product_collection.collection = 'Data'
                elif collection == 'browse':
                    product_collection.collection = 'Browse'
                elif collection == 'geometry':
                    product_collection.collection = 'Geometry'
                elif collection == 'calibration':
                    product_collection.collection = 'Calibration'
                product_collection.save()
                print '\n\n{} Collection Directory:    {}'.format(collection, product_collection.directory())

                # Build Product_Collection label for all labels other than those found in the data collection.
                print '-------------Start Build Product_Collection Base Case-----------------'
                if collection != 'data':
                    product_collection.build_base_case()

                    # Open Product_Collection label
                    print ' ... Opening Label ... '
                    label_list = open_label(product_collection.label())
                    label_object = label_list[0]
                    label_root = label_list[1]

                    # Fill label
                    print ' ... Filling Label ... '
                    label_root = product_collection.fill_base_case(label_root)

                    # Close label
                    print ' ... Closing Label ... '
                    close_label(label_object, label_root)
                    print '-------------End Build Product_Collection Base Case-----------------'
           
            # Further develop context_dict entries for templates            
            context_dict['Bundle'] = bundle
            context_dict['Product_Bundle'] = Product_Bundle.objects.get(bundle=bundle)
            context_dict['Product_Collection_Set'] = Product_Collection.objects.filter(bundle=bundle)

            return render(request, 'build/two.html', context_dict)

    return render(request, 'build/build.html', context_dict)









# The bundle_detail view is the page that details a specific bundle.
@login_required
def bundle(request, pk_bundle):
    # Get Bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)
        # ELSA's current user is the bundle user so begin view logic

        print ' \n\n \n\n----------------------------------------------------------------------\n'
        print '-----------------------BEGIN Bundle Detail VIEW--------------------------.\n'
        print '--------------------------------------------------------------------------\n'
        context_dict = {
            'bundle':bundle,
            'collections': Collections.objects.get(bundle=bundle),
        }
        return render(request, 'build/bundle/bundle.html', context_dict)

    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')



# The bundle_download view is not a page.  When a user chooses to download a bundle, this 'view' manifests and begins the downloading process.
def bundle_download(request, pk_bundle):    
    # Get Bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        # ELSA's current user is the bundle user so begin view logic
        print '----------------------------------------------------------------------------------\n'
        print '------------------------------ START BUNDLE DOWNLOAD -----------------------------\n'
        print '----------------------------------------------------------------------------------\n'

        print '\n\n------------------------------- BUNDLE INFO -------------------------------'
        print 'Bundle User: {}'.format(bundle.user)
        print 'Bundle Directory: {}'.format(bundle.directory())
        print 'Current Working Directory: {}'.format(os.getcwd())
        print 'Temporary Directory: {}'.format(settings.TEMPORARY_DIR)
        print 'Archive Directory: {}'.format(settings.ARCHIVE_DIR)

        # Make tarfile
        #    Note: This does not run in build directory, it runs in the elsa project directory, where manage.py lives.  
        tar_bundle_dir = '{}.tar.gz'.format(bundle.directory())
        temp_dir = os.path.join(settings.TEMPORARY_DIR, tar_bundle_dir)
        source_dir = os.path.join(settings.ARCHIVE_DIR, bundle.user.username)
        source_dir = os.path.join(source_dir, bundle.directory())
        make_tarfile(temp_dir, source_dir)

        # Testing.  See if simply bundle directory will download.
        # Once finished, make directory a tarfile and then download.
        file_path = os.path.join(settings.TEMPORARY_DIR, tar_bundle_dir)


        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/x-tar")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response

        return HttpResponse("Download did not work.")

    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')










# The bundle_delete view is the page a user sees once they select the delete bundle button.  This view gives the user an option to confirm or take back their choice.  This view could be improved upon.
@login_required
def bundle_delete(request, pk_bundle):


    # Get Bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        # ELSA's current user is the bundle user so begin view logic
        print '\n\n'
        print '---------------------------------------------------------------------------------\n'
        print '---------------------- Start Bundle Delete --------------------------------------\n'
        print '---------------------------------------------------------------------------------\n'


        print '\n\n------------------------------- BUNDLE INFO -------------------------------'
        print 'Bundle: {}'.format(bundle)
        print 'User: {}'.format(bundle.user)
	print 'Request: {}'.format(request.user)

        confirm_form = ConfirmForm(request.POST or None)
        context_dict = {}
        context_dict['bundle'] = bundle
        context_dict['user'] = bundle.user
        context_dict['delete_bundle_form'] = confirm_form   # CHANGE CONTEXT_DICT KEY TO 'confirm_form' #
        context_dict['user_response'] = 'empty'


        print 'Form confirm_form is valid: {}'.format(confirm_form.is_valid())
        print 'Response user_response is: {}'.format(context_dict['user_response'])
        if confirm_form.is_valid():
            print 'Delete Bundle? {}'.format(confirm_form.cleaned_data["decision"])
            decision = confirm_form.cleaned_data['decision']
            if decision == 'Yes':
                context_dict['decision'] = 'was'
                success_status = bundle.remove_bundle()
		bundle.delete()
                if success_status:
                    return redirect('../../success_delete/')


            if decision == 'No':
                # Go back to bundle page
                context_dict['decision'] = 'was not'

        return render(request, 'build/bundle/confirm_delete.html', context_dict)

    # Secure: Current user is not the user associated with the bundle, so...
    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')


def success_delete(request):
    return render(request, 'build/bundle/success_delete.html')











def citation_information(request, pk_bundle):
    print '\n\n'
    print '-------------------------------------------------------------------------'
    print '\n\n--------------- Add Citation_Information with ELSA -------------------'
    print '------------------------------ DEBUGGER ---------------------------------'


    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        # Get forms
        form_citation_information = CitationInformationForm(request.POST or None)

        # Declare context_dict for template
        context_dict = {
            'form_citation_information':form_citation_information,
            'bundle':bundle,

        }

        # After ELSAs friend hits submit, if the forms are completed correctly, we should enter
        # this conditional.
        print '\n\n----------------- CITATION_INFORMATION INFO -------------------------'
        if form_citation_information.is_valid():
            print 'form_citation_information is valid'
            # Create Citation_Information model object
            citation_information = form_citation_information.save(commit=False)
            citation_information.bundle = bundle
            citation_information.save()
            print 'Citation Information model object: {}'.format(citation_information)

            # Find appropriate label(s).  Citation_Information gets added to all Product_Bundle and 
            # Product_Collection labels in a Bundle.  The Data collection is excluded since it is 
            # handled different from the other collections.
            all_labels = []
            product_bundle = Product_Bundle.objects.get(bundle=bundle)
            product_collections_list = Product_Collection.objects.filter(bundle=bundle).exclude(collection='Data')
            all_labels.append(product_bundle)             # Append because a single item
            all_labels.extend(product_collections_list)   # Extend because a list

            for label in all_labels:

                # Open appropriate label(s).  
                print '- Label: {}'.format(label)
                print ' ... Opening Label ... '
                label_list = open_label(label.label())
                label_object = label_list[0]
                label_root = label_list[1]
        
                # Build Citation Information
                print ' ... Building Label ... '
                label_root = citation_information.build_citation_information(label_root)

                # Close appropriate label(s)
                print ' ... Closing Label ... '
                close_label(label_object, label_root)

                print '------------- End Build Citation Information -------------------'        
        # Update context_dict with the current Citation_Information models associated with the user's bundle
        context_dict['citation_information_set'] = Citation_Information.objects.filter(bundle=bundle)
        return render(request, 'build/citation_information/citation_information.html',context_dict)

    # Secure: Current user is not the user associated with the bundle, so...
    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')











@login_required
def data(request, pk_bundle): 
    print '\n\n'
    print '-------------------------------------------------------------------------'
    print '\n\n---------------------- Add Data with ELSA ---------------------------'
    print '------------------------------ DEBUGGER ---------------------------------'

    # Get bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        # Get forms
        form_data = DataForm(request.POST or None)
        form_product_observational = ProductObservationalForm(request.POST or None)

        # Context Dictionary
        context_dict = {
            'bundle':bundle,
            'form_data':form_data,
            'form_product_observational':form_product_observational,
        }
        # After ELSAs friend hits submit, if the forms are completed correctly, we should enter
        # this conditional.
        print '\n\n------------------------ DATA INFO ----------------------------------'
        if form_data.is_valid() and form_product_observational.is_valid():

            # Create Data model object
            data = form_data.save(commit=False)
            data.bundle = bundle
            data.save()
            print 'Data model object: {}'.format(data)

            # Create Product_Observational model object
            product_observational = form_product_observational.save(commit=False)
            product_observational.bundle = bundle
            product_observational.data = data
            product_observational.processing_level = data.processing_level
            product_observational.save()
            print 'Product_Observational model object: {}'.format(product_observational)

            # Create Data Folder corresponding to processing level
            data.build_directory()

            print '---------------- Start Build Product_Collection Base Case ------------------------'
            product_collection = Product_Collection.objects.get(bundle=bundle, collection='Data')
            product_collection.build_base_case_data(data)
        
            print '---------------- End Build Product_Collection Base Case -------------------------'
                


            print '---------------- Start Build Product_Observational Base Case ---------------------'
            # Copy Product_Observational label
            product_observational.build_base_case()

            # Open label - returns a list of label information where list = [label_object, label_root]
            print ' ... Opening Label ... '
            label_list = open_label(product_observational.label())
            label_object = label_list[0]
            label_root = label_list[1]
            # Fill label - fills 
            print ' ... Filling Label ... '
            label_root = product_observational.fill_base_case(label_root)
            # Close label
            print ' ... Closing Label ... '
            close_label(label_object, label_root)           
            print '---------------- End Build Product_Observational Base Case-----------------------'

            # Update context_dict
            print '\n\n---------------------- UPDATING CONTEXT DICTIONARY --------------------------'
            context_dict['data'] = data
            context_dict['product_observational'] = product_observational  # Needs a fix
        
        data_set = Data.objects.filter(bundle=bundle)
        context_dict['data_set'] = data_set
        product_observational_set = []
        for data in data_set:
            product_observational_set.extend(Product_Observational.objects.filter(data=data))
        context_dict['product_observational_set'] = product_observational_set
      
        return render(request, 'build/data/data.html', context_dict)

    # Secure: Current user is not the user associated with the bundle, so...
    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')















def document(request, pk_bundle):
    print '\n\n'
    print '-------------------------------------------------------------------------'
    print '\n\n--------------------- Add Document with ELSA ------------------------'
    print '------------------------------ DEBUGGER ---------------------------------'

    # Get bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        # Get forms
        form_product_document = ProductDocumentForm(request.POST or None)

        # Declare context_dict for template
        context_dict = {
            'form_product_document':form_product_document,
            'bundle':bundle,

        }

        # After ELSAs friend hits submit, if the forms are completed correctly, we should enter
        # this conditional.  We must do [] things: 1. Create the Document model object, 2. Add a Product_Document label to the Document Collection, 3. Add the Document as an Internal_Reference to the proper labels (like Product_Bundle and Product_Collection).
        print '\n\n---------------------- DOCUMENT INFO -------------------------------'
        if form_product_document.is_valid():
            print 'form_product_document is valid'  

            # Create Document Model Object
            product_document = form_product_document.save(commit=False)
            product_document.bundle = bundle
            product_document.save()
            print 'Product_Document model object: {}'.format(product_document)

            # Build Product_Document label using the base case template found
            # in templates/pds4/basecase
            print '\n---------------Start Build Product_Document Base Case------------------------'
            product_document.build_base_case()
            # Open label - returns a list where index 0 is the label object and 1 is the tree
            print ' ... Opening Label ... '
            label_list = open_label(product_document.label())
            label_object = label_list[0]
            label_root = label_list[1]
            # Fill label - fills 
            print ' ... Filling Label ... '
            label_root = product_document.fill_base_case(label_root)
            # Close label    
            print ' ... Closing Label ... '
            close_label(label_object, label_root)           
            print '---------------- End Build Product_Document Base Case -------------------------' 

            # Add Document info to proper labels.  For now, I simply have Product_Bundle and Product_Collection.  This list will need to be updated.
            print '\n---------------Start Build Internal_Reference for Document-------------------'
            all_labels = []
            product_bundle = Product_Bundle.objects.get(bundle=bundle)
            product_collections_list = Product_Collection.objects.filter(bundle=bundle)

            all_labels.append(product_bundle)
            all_labels.extend(product_collections_list)  

            for label in all_labels:
                print '- Label: {}'.format(label)
                print ' ... Opening Label ... '
                label_list = open_label(label.label())
                label_object = label_list[0]
                label_root = label_list[1]
        
                # Build Internal_Reference
                print ' ... Building Internal_Reference ... '
                label_root = label.build_internal_reference(label_root, product_document)

                # Close appropriate label(s)
                print ' ... Closing Label ... '
                close_label(label_object, label_root)
            print '\n----------------End Build Internal_Reference for Document-------------------'


        context_dict['documents'] = Product_Document.objects.filter(bundle=bundle)    
        return render(request, 'build/document/document.html',context_dict)

    # Secure: Current user is not the user associated with the bundle, so...
    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')

 










def product_observational(request, pk_bundle, pk_product_observational):
    print '\n\n'
    print '-------------------------------------------------------------------------'
    print '\n\n---------------- Add Product_Observational with ELSA ----------------'
    print '------------------------------ DEBUGGER ---------------------------------'


    # Get bundle
    bundle = Bundle.objects.get(pk=pk_bundle)

    # Secure ELSA by seeing if the user logged in is the same user associated with the Bundle
    if request.user == bundle.user:
        print 'authorized user: {}'.format(request.user)

        product_observational = Product_Observational.objects.get(pk=pk_product_observational)
        form_product_observational = TableForm(request.POST or None)
        context_dict = {
            'bundle':bundle,
            'product_observational':product_observational,
            'form_product_observational':form_product_observational,

        }

        print '\n\n----------------- PRODUCT_DOCUMENT INFO -----------------------------'
        if form_product_observational.is_valid():
            print 'form_product_observational is valid.'
            # Create the associated model (Table, Array, Cube, etc...)
            observational = form_product_observational.save(commit=False)
            observational.product_observational = product_observational
            observational.save()
            print 'observational object: {}'.format(observational)
        

            print '\n--------- Start Add Observational to Product_Observational -----------------'
            # Open label
            print ' ... Opening Label ... '
            label_list = open_label(product_observational.label())
            label_object = label_list[0]
            label_root = label_list[1]
            print label_root

            # Fill label
            print ' ... Filling Label ... '
            label_root = product_observational.fill_observational(label_root, observational)

            # Close label
            print ' ... Closing Label ... '
            close_label(label_object, label_root)
            print '-------------End Add Observational to Product_Observational -----------------'
        
        # Now we must grab the observational set to display on ELSA's template for the Product_Observational page.  Right now, this is tables so it is easy.
        observational_set = Table.objects.filter(product_observational=product_observational)
        context_dict['observational_set'] = observational_set
    
        return render(request, 'build/data/table.html', context_dict)

    # Secure: Current user is not the user associated with the bundle, so...
    else:
        print 'unauthorized user attempting to access a restricted area.'
        return redirect('main:restricted_access')
